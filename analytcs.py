'''import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# Путь к папке скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))

# Поиск всех CSV файлов в папке скрипта
csv_files = glob.glob(os.path.join(script_dir, '*.csv'))

# Чтение и объединение всех CSV
data_list = []
for file in csv_files:
    df = pd.read_csv(file)
    data_list.append(df)

# Объединяем все в один датафрейм
data = pd.concat(data_list, ignore_index=True)

# Преобразование времени
data['EVENT_TIMESTAMP'] = pd.to_datetime(data['EVENT_TIMESTAMP'])

# Сортировка по пользователю и времени
data_sorted = data.sort_values(['USER_ID', 'EVENT_TIMESTAMP'])

# Группировка по пользователю и расчет длительности сессии
sessions = []
for user_id, group in data_sorted.groupby('USER_ID'):
    start_time = group['EVENT_TIMESTAMP'].iloc[0]
    end_time = group['EVENT_TIMESTAMP'].iloc[-1]
    duration = (end_time - start_time).total_seconds() / 60  # в минутах
    if duration < 5 or duration > 100:
        continue
    sessions.append(duration)

# Расчет доли долгоиграющих
long_playing_in_sample = len(sessions)

unique_users = data['USER_ID'].nunique()
print(f"Уникальных пользователей: {unique_users}")
print(f"Количество игроков в выборке: {len(sessions)}")

# Построение гистограммы
plt.figure(figsize=(10, 6))
plt.hist(sessions, bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Длительность сессии (минуты)')
plt.ylabel('Количество игроков')
plt.title('Распределение игроков по длительности сессии')
plt.grid(True)
plt.show()'''