import time, json, requests
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import MaxNLocator


API_URL = "https://api.plancke.io/hypixel/v1/punishmentStats"
HEADERS = {"User-Agent": "Mozilla/5.0"}

HOUR_FILE = "hour_data.txt"
DAY_FILE = "day_data.txt"
HOUR_GRAPH = "staff_bans_hour.png"
DAY_GRAPH = "staff_bans_day.png"


def send_discord_image_pair(hour_path, day_path):
    with open(hour_path, "rb") as f1, open(day_path, "rb") as f2:
        files = {
            "files[0]": ("staff_bans_hour.png", f1, "image/png"),
            "files[1]": ("staff_bans_day.png", f2, "image/png"),
        }

        data = {
            "embeds": [
                {
                    "title": "Staff bans for the last hour",
                    "color": 14221148,
                    "image": {
                        "url": "attachment://staff_bans_hour.png"
                    }
                },
                {
                    "title": "Staff bans for the last day",
                    "color": 16767327,
                    "image": {
                        "url": "attachment://staff_bans_day.png"
                    }
                }
            ]
        }

        response = requests.post(
            "https://discord.com/api/webhooks/1378825941983301794/pIGjKoYjecZ7_maoHFsDR60bAChaDP8agkBKz5TR-0MO4sR9ex_hxTm6ia9vWteWkJAX",
            data={"payload_json": json.dumps(data)},
            files=files
        )

        if response.status_code in (200, 204):
            print("Эмбеды с изображениями успешно отправлены в Discord.")
        else:
            print(f"Ошибка при отправке: {response.status_code} - {response.text}")


def fetch_staff_total():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if data.get("success") and "record" in data:
                return data["record"]["staff_total"]
    except Exception as e:
        print(f"Ошибка запроса: {e}")
    return None


def append_to_file(filename, timestamp, value, date_str):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{date_str} {timestamp} {value}\n")


def read_data_from_file(filename, filter_date=None, filter_hour=None):
    times = []
    values = []

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3:
                    date_part, time_part, val = parts
                    if filter_date and date_part != filter_date:
                        continue
                    if filter_hour and time_part.split(":")[0] != filter_hour:
                        continue
                    times.append(time_part)
                    values.append(int(val))
    except FileNotFoundError:
        pass

    return times, values

def clear_file(filename):
    try:
        open(filename, "w", encoding="utf-8").close()
    except Exception as e:
        print(f"Ошибка при очистке файла {filename}: {e}")


def plot_graph(times, values, title, xlabel, ylabel, filename):
    plt.figure(figsize=(12, 5))
    plt.plot(times, values, color='blue', marker='o', linestyle='-', linewidth=2)
    plt.xticks(rotation=45)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)

    ax = plt.gca()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def main_loop():
    prev_staff_total = None
    last_hour = datetime.now().hour
    last_day = datetime.now().day

    while True:
        now_dt = datetime.now()
        now_str = now_dt.strftime("%H:%M")
        date_str = now_dt.strftime("%Y-%m-%d")
        current_hour_str = now_dt.strftime("%H")

        if now_dt.hour != last_hour:
            clear_file(HOUR_FILE)
            last_hour = now_dt.hour

        if now_dt.day != last_day:
            clear_file(DAY_FILE)
            last_day = now_dt.day

        current_staff_total = fetch_staff_total()
        if current_staff_total is None:
            print(f"[{now_str}] Не удалось получить данные.")
            time.sleep(60)
            continue

        if prev_staff_total is not None:
            diff = current_staff_total - prev_staff_total

            append_to_file(HOUR_FILE, now_str, diff, date_str)
            append_to_file(DAY_FILE, now_str, diff, date_str)

            hour_times, hour_values = read_data_from_file(HOUR_FILE, filter_date=date_str, filter_hour=current_hour_str)
            day_times, day_values = read_data_from_file(DAY_FILE, filter_date=date_str)

            plot_graph(
                hour_times, hour_values,
                "Баны стаффа за последний час",
                "Время",
                "Количество банов",
                HOUR_GRAPH
            )

            plot_graph(
                day_times, day_values,
                "Баны стаффа за последние сутки",
                "Время",
                "Количество банов",
                DAY_GRAPH
            )

            print(f"[{now_str}] За последнюю минуту забанили: {diff}")

            if now_dt.minute == 0:
                send_discord_image_pair(HOUR_GRAPH, DAY_GRAPH)

        prev_staff_total = current_staff_total
        time.sleep(60)


if __name__ == "__main__":
    main_loop()
