from multiprocessing import Pool

import pytz
from django.core.files.uploadedfile import InMemoryUploadedFile
from fitparse import FitFile
from tzwhere import tzwhere

from app.models import Activity, Lap, Record, PowerCurveEntry


class FITParser:
    activity_data = None
    activity = None
    records = None
    laps = None
    power = None
    tz_offset = None
    decoded = None

    def parse_fit(self, file: InMemoryUploadedFile):
        # TODO: Bulk update?
        self.decoded = FitFile(file.read())

        records = [r for r in self.decoded.get_messages(name='record')]
        self.set_offset()

        self.load_records(records)

        self.load_activity()

        self.load_laps()

        Lap.objects.bulk_create(self.laps)

        for j in range(len(self.laps)):
            for i in range(self.laps[j].record_start, self.laps[j].record_end + 1):
                self.records[i].activity = self.activity
                self.records[i].lap = self.laps[j]

        Record.objects.bulk_create(self.records)

    def set_offset(self):
        self.activity_data = [r for r in self.decoded.get_messages(name='session')][0]

        lat = self.activity_data.get_value('start_position_lat') * 180 / 2 ** 31
        long = self.activity_data.get_value('start_position_long') * 180 / 2 ** 31

        tzw = tzwhere.tzwhere()
        tz = pytz.timezone(tzw.tzNameAt(lat, long))
        start_time = self.activity_data.get_value('start_time')

        self.tz_offset = tz.utcoffset(start_time)

    def find_max(self, k):
        t = sum(self.power[:k])
        m = t

        for i in range(len(self.records) - k):
            t -= self.power[i]
            t += self.power[i + k]
            if t > m:
                m = t

        return {'duration': k, 'power': m / k}

    def load_curve(self):
        activity_curve = [0 for _ in range(len(self.records) // 5 + 1)]
        self.power = [r.power for r in self.records]

        pool = Pool(processes=4)
        activity_curve = pool.map(self.find_max, [1 if a == 0 else a * 5 for a in range(len(activity_curve))])
        pool.join()
        pool.close()
        activity_curve = sorted(activity_curve, key=lambda x: x['duration'])
        print(activity_curve)
        print(self.activity.max_power)

        power_curve = PowerCurveEntry.objects.all()

        i = 0
        while i < len(power_curve) and i < len(activity_curve):
            if activity_curve[i] > power_curve[i].power:
                power_curve[i].power = activity_curve[i]
                power_curve[i].activity = self.activity
                power_curve[i].save()
            i += 1

        for i in range(len(power_curve), len(activity_curve)):
            entry = PowerCurveEntry()
            entry.activity = self.activity
            entry.power = activity_curve[i]
            entry.duration = 1 if i < 1 else i * 5
            entry.save()

    def load_activity(self):
        self.activity = Activity(
            start_time=pytz.utc.localize(self.activity_data.get_value('start_time') + self.tz_offset),
            elapsed_time=self.activity_data.get_value('total_elapsed_time'),
            start_position_lat=self.activity_data.get_value('start_position_lat'),
            start_position_long=self.activity_data.get_value('start_position_long'),
            timer_time=self.activity_data.get_value('total_timer_time'),
            distance=self.activity_data.get_value('total_distance'),
            strides=self.activity_data.get_value('total_strides'),
            speed=self.activity_data.get_value('enhanced_avg_speed'),
            max_speed=self.activity_data.get_value('enhanced_max_speed'),
            calories=self.activity_data.get_value('total_calories'),
            ascent=self.activity_data.get_value('total_ascent'),
            descent=self.activity_data.get_value('total_descent'),
            lap_count=self.activity_data.get_value('num_laps'),
            heart_rate=self.activity_data.get_value('avg_heart_rate'),
            max_heart_rate=self.activity_data.get_value('max_heart_rate'),
            cadence=self.activity_data.get_value('avg_running_cadence'),
            max_cadence=self.activity_data.get_value('max_running_cadence'),
            aerobic_training_effect=self.activity_data.get_value('total_training_effect'),
            anaerobic_training_effect=self.activity_data.get_value('total_anaerobic_training_effect'),
            max_power=0,
            power=0
        )

        for r in self.records:
            if r.power > self.activity.max_power:
                self.activity.max_power = r.power
            self.activity.power += r.power

        self.activity.power /= len(self.records)

        self.activity.save()

    def load_laps(self):
        self.laps = [
            Lap(
                activity=self.activity,
                start_time=pytz.utc.localize(lap.get_value('start_time') + self.tz_offset),
                end_time=pytz.utc.localize(lap.get_value('timestamp') + self.tz_offset),
                start_position_lat=lap.get_value('start_position_lat'),
                start_position_long=lap.get_value('start_position_long'),
                end_position_lat=lap.get_value('end_position_lat'),
                end_position_long=lap.get_value('end_position_long'),
                elapsed_time=lap.get_value('total_elapsed_time'),
                timer_time=lap.get_value('total_timer_time'),
                distance=lap.get_value('total_distance'),
                strides=lap.get_value('total_strides'),
                speed=lap.get_value('enhanced_avg_speed'),
                max_speed=lap.get_value('enhanced_max_speed'),
                calories=lap.get_value('total_calories'),
                ascent=lap.get_value('total_ascent'),
                descent=lap.get_value('total_descent'),
                heart_rate=lap.get_value('avg_heart_rate'),
                max_heart_rate=lap.get_value('max_heart_rate'),
                cadence=lap.get_value('avg_running_cadence'),
                max_cadence=lap.get_value('max_running_cadence'),
                lap_trigger=lap.get_value('lap_trigger'),
                power=lap.get_value('Lap Power')
            )
            for lap in self.decoded.get_messages(name='lap')
        ]

        for lap in self.laps:
            ground_time = 0
            air_power = 0
            form_power = 0

            j = 0
            while j < len(self.records) and self.records[j].timestamp < lap.start_time:
                j += 1
            lap.record_start = j
            while j < len(self.records) and self.records[j].timestamp <= lap.end_time:
                ground_time += self.records[j].ground_time
                air_power += self.records[j].air_power
                form_power += self.records[j].form_power
                j += 1
            if j == lap.record_start:
                break
            lap.record_end = j - 1
            lap.ground_contact = ground_time / lap.timer_time
            lap.air_power = air_power / lap.timer_time
            lap.form_power = form_power / lap.timer_time

    def load_records(self, records):
        self.records = [
            Record(
                timestamp=pytz.utc.localize(r.get_value('timestamp') + self.tz_offset),
                position_lat=r.get_value('position_lat') * 180 / (2 ** 31),
                position_long=r.get_value('position_long') * 180 / (2 ** 31),
                distance=r.get_value('distance'),
                speed=r.get_value('enhanced_speed'),
                altitude=r.get_value('enhanced_altitude'),
                heart_rate=r.get_value('heart_rate'),
                cadence=r.get_value('cadence'),
                power=r.get_value('Power'),
                ground_time=r.get_value('Ground Time'),
                air_power=r.get_value('Air Power'),
                form_power=r.get_value('Form Power'),
            )
            for r in records if r.name == 'record'
        ]
