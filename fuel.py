import krpc
import time
import json

# Подключаемся к серверу kRPC
conn = krpc.connect()
vessel = conn.space_center.active_vessel


# Функция для записи данных в JSON-файл
def write_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)


# Инициализируем список для хранения данных о топливе
fuel_data_log = []

# Имя выходного файла для данных о топливе
fuel_output_file = 'rocket_current_stage_fuel.json'

print("Сбор данных о массе топлива текущей ступени начался. Нажмите Ctrl+C для завершения.")

try:
    while True:
        # Получаем текущее время миссии
        mission_time = vessel.met

        # Получаем текущую ступень
        current_stage = vessel.control.current_stage

        # Получаем ресурсы текущей ступени
        stage_resources = conn.space_center.Resources(vessel, stage=current_stage)

        # Основные типы топлива для ракет
        main_fuel_types = ['LiquidFuel', 'SolidFuel', 'Oxidizer']

        # Подсчитываем общую массу топлива в текущей ступени
        stage_fuel_mass = 0.0

        for fuel_type in main_fuel_types:
            if stage_resources.has_resource(fuel_type):
                stage_fuel_mass += stage_resources.amount(fuel_type)

        # Также получаем общую массу всего топлива на корабле для сравнения
        total_resources = vessel.resources
        total_fuel_mass = 0.0

        for fuel_type in main_fuel_types:
            if total_resources.has_resource(fuel_type):
                total_fuel_mass += total_resources.amount(fuel_type)

        # Добавляем данные в список
        fuel_data_log.append({
            'time': mission_time,
            'current_stage': current_stage,
            'stage_fuel_mass_kg': stage_fuel_mass,
            'total_fuel_mass_kg': total_fuel_mass,
            'fuel_percentage': (stage_fuel_mass / total_fuel_mass * 100) if total_fuel_mass > 0 else 0
        })

        # Ждём 1 секунду перед следующей записью
        time.sleep(1)

except KeyboardInterrupt:
    # При завершении записи сохраняем данные в файл
    print(f"\nСохранение {len(fuel_data_log)} записей в файл...")
    write_to_json(fuel_output_file, fuel_data_log)
    print(f"Данные сохранены в {fuel_output_file}")