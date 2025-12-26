from datetime import datetime, date
from icalendar import Calendar
import pytz
import argparse

ICS_FILE = "calendar.ics"


def to_utc(dt):
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return None

    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)

    return dt.astimezone(pytz.UTC)


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate calendar income")
    parser.add_argument(
        "--rate",
        type=float,
        required=True,
        help="Hourly rate in denars",
    )
    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    return parser.parse_args()


def format_denars(amount):

    return f"{int(amount):,}".replace(",", " ")


def main():
    args = parse_args()

    hourly_rate = args.rate

    start_date = pytz.UTC.localize(
        datetime.strptime(args.start, "%Y-%m-%d")
    )
    end_date = pytz.UTC.localize(
        datetime.strptime(args.end, "%Y-%m-%d")
    ).replace(hour=23, minute=59, second=59)

    events = []
    all_day_events = []

    with open(ICS_FILE, "rb") as f:
        calendar = Calendar.from_ical(f.read())

    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")

        if not dtstart or not dtend:
            continue

        start = to_utc(dtstart.dt)
        end = to_utc(dtend.dt)
        summary = component.get("SUMMARY", "No title")

        if start is None or end is None:
            all_day_events.append({
                "date": dtstart.dt,
                "summary": summary
            })
            continue

        if not (start_date <= start <= end_date):
            continue

        duration_hours = (end - start).total_seconds() / 3600
        if duration_hours <= 0:
            continue

        value = duration_hours * hourly_rate

        events.append(
            {
                "start": start,
                "summary": summary,
                "hours": duration_hours,
                "value": value,
            }
        )

    events.sort(key=lambda e: e["start"])

    total_value = 0.0

    for e in events:
        total_value += e["value"]
        print(
            f"{e['start'].date()} | "
            f"{e['summary']} | "
            f"{e['hours']:.2f}h | "
            f"{format_denars(e['value'])} denars"
        )

    print("\n" + "-" * 50)
    print(f"TOTAL EVENTS : {len(events)}")
    print(f"TOTAL VALUE  : {format_denars(total_value)} denars")

    if all_day_events:
        print("\n" + "=" * 50)
        print("ALL-DAY EVENTS (not included in calculation):")
        print("=" * 50)
        for e in all_day_events:
            print(f"{e['date']} | {e['summary']}")
        print(f"\nTotal all-day events: {len(all_day_events)}")


if __name__ == "__main__":
    main()