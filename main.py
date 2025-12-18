import numpy as np # реализует математические функции
import matplotlib.pyplot as plt # отвечает за построение графиков
import json

# КОНСТАНТЫ
G = 6.67430e-11  # гравитационная постоянная, м³·кг⁻¹·с⁻²
M_z = 5.292 * 10 ** 22   # масса Земли, кг
R_z = 600000  # радиус Земли, м
g0 = 9.81  # ускорение свободного падения у поверхности, м/с²
M_air = 0.028965  # молярная масса воздуха, кг/моль
R_gas = 8.314  # газовая постоянная, Дж/(моль·К)
T_atm = 288  # температура воздуха, К 14.5С
p0 = 101325  # давление на уровне моря, Па

# ХАРАКТЕРИСТИКИ СТУПЕНЕЙ РАКЕТЫ
stages = [
    {  # Первая ступень
        'm0': 106000 + 59844,  # начальная масса ступени, кг
        'mt': 59844,  # масса топлива, кг
        't_stage': 29,  # время работы, с
        'I_sea': 250,  # удельный импульс на уровне моря, с
        'I_vac': 300,  # удельный импульс в вакууме, с
        'S': 10,  # площадь поперечного сечения, м²
        'Cx': 0.3  # коэффициент лобового сопротивления
    },
    {  # Вторая ступень
        'm0': 17303 + 50303,
        'mt': 50303,
        't_stage': 210,
        'I_vac': 154,
        'S': 10,
        'Cx': 0.3
    },
    {  # Третья ступень
        'm0': 3361 + 4019,
        'mt': 4019,
        't_stage': 60,
        'I_vac': 290,
        'S': 10,
        'Cx': 0.3
    }
]


def theta(t): #угол между тягой и вертикалью
    if t < 20:
        return np.deg2rad(5)  # 5°(Преобразует углы из градусов в радианы)
    elif t < 60:
        return np.deg2rad(15)  # 15°
    else:
        return np.deg2rad(30)  # 30°


def rho(h, g_h): # зависимость плотности воздуха от высоты
    if h <= 0:
        h = 0
    p_h = p0 * np.exp(-M_air * g_h * h / (R_gas * T_atm))
    return p_h * M_air / (R_gas * T_atm)


# НАЧАЛЬНЫЕ УСЛОВИЯ
t_total = sum(stage['t_stage'] for stage in stages)  # общее время полёта
dt = 0.1
t = np.arange(0, 250, dt)

# " Массивы результатов
h = np.zeros_like(t)  # высота, м
vx = np.zeros_like(t)  # горизонтальная скорость, м/с
vy = np.zeros_like(t)  # вертикальная скорость, м/с
v = np.zeros_like(t)  # модуль скорости, м/с
m = np.zeros_like(t)  # масса, кг
ax = np.zeros_like(t)  # горизонтальное ускорение, м/с²
ay = np.zeros_like(t)  # вертикальное ускорение, м/с²
stage_idx = np.zeros_like(t, dtype=int)  # номер текущей ступени

# " Начальные значения
h[0] = 0
vx[0] = 0
vy[0] = 0
m[0] = stages[0]['m0']
current_stage = 0
t_stage_start = 0


for i in range(1, len(t)):
    t_curr = t[i]
    # определяем текущую ступень
    while current_stage < len(stages) and t_curr >= t_stage_start + stages[current_stage]['t_stage']:
        t_stage_start += stages[current_stage]['t_stage']
        current_stage += 1

    if current_stage >= len(stages):
        current_stage = len(stages) - 1  # последняя ступень до конца

    stage = stages[current_stage]
    stage_idx[i] = current_stage

    t_in_stage = t_curr - t_stage_start

    # масса линейно уменьшаеттся при сжигании топлива, и резкий скачок вниз при отбросе ступени
    if t_in_stage <= stage['t_stage']:
        m[i] = stage['m0'] - (stage['mt'] / stage['t_stage']) * t_in_stage
    else:
        # Уже перешли на следующую ступень — масса скачком уменьшилась
        m[i] = stage['m0'] - stage['mt']

    g_h = G * M_z / (R_z + h[i - 1]) ** 2  # ускорение свободного падения на текущей высоте
    rho_h = rho(h[i - 1], g_h) # плотность воздуха
    v[i] = np.sqrt(vx[i - 1] ** 2 + vy[i - 1] ** 2) # модуль скорости

    # расчёт удельного импульса
    if current_stage == 0:
        if t_in_stage < 30:
            I = stage['I_sea']
        else:
            I = stage['I_vac']
    else:
        I = stage['I_vac']

    F_thrust = I * (stage['mt'] / stage['t_stage']) * g0  # сила тяги
    # проекции силы тяги
    theta_t = theta(t_curr)
    F_thrust_x = F_thrust * np.sin(theta_t)
    F_thrust_y = F_thrust * np.cos(theta_t)

    F_gravity = m[i] * g_h # сила тяжести
    F_drag = 0.5 * stage['Cx'] * rho_h * stage['S'] * v[i] ** 2 # сила сопротивленияя

    # проекции (противоположно скорости)
    if v[i] > 0:
        F_drag_x = -F_drag * (vx[i - 1] / v[i])
        F_drag_y = -F_drag * (vy[i - 1] / v[i])
    else:
        F_drag_x, F_drag_y = 0.0, 0.0

    # ускорения (по осям)
    ax[i] = (F_thrust_x + F_drag_x) / m[i]
    ay[i] = (F_thrust_y - F_gravity + F_drag_y) / m[i]

    # обновление скоростей и высоты
    vx[i] = vx[i - 1] + ax[i] * dt
    vy[i] = vy[i - 1] + ay[i] * dt
    h[i] = h[i - 1] + vy[i] * dt


with open("масса2.json", encoding="UTF-8") as f:
    sl_mass = json.load(f)
mass_ksp = [elem['mass'] for elem in sl_mass if elem["time"] <= 250]
mass_ksp_t = [elem['time'] for elem in sl_mass if elem["time"] <= 250]

with open("высота2.json", encoding="UTF-8") as f:
    sl_height = json.load(f)
height_ksp = [elem['height'] for elem in sl_height if elem["time"] <= 250]
height_ksp_t = [elem['time'] for elem in sl_height if elem["time"] <= 250]

with open("скорость2.json", encoding="UTF-8") as f:
    sl_speed = json.load(f)
speed_ksp = [elem['speed'] for elem in sl_speed if elem["time"] <= 250]
speed_ksp_t = [elem['time'] for elem in sl_speed if elem["time"] <= 250]


# ПОСТРОЕНИЕ ГРАФИКОВ
fig, axs = plt.subplots(3, 1, figsize=(12, 14))
fig.suptitle('Графики зависимости высоты, скорости и массы от времени', fontsize=16)

# Высота
axs[0].plot(t, h, label='Мат. модель', color='red')
axs[0].plot(height_ksp_t, height_ksp, label="KSP", color="green")
axs[0].set_xlabel('Время, с')
axs[0].set_ylabel('Высота, м')
axs[0].set_title('Высота полёта, м')
axs[0].grid(True, linestyle='--', alpha=0.7)
axs[0].legend()

# Скорость
axs[1].plot(t, v, label='Мат. модель', color='red')
axs[1].plot(speed_ksp_t, speed_ksp, label="KSP", color="green", alpha=0.7)
axs[1].set_xlabel('Время, с')
axs[1].set_ylabel('Скорость, м/с')
axs[1].grid(True, linestyle='--', alpha=0.7)
axs[1].set_title('Скорость полёта, м/с')
axs[1].legend()

# Масса
axs[2].plot(t, m, label='Мат. модель', color='red')
axs[2].plot(mass_ksp_t, mass_ksp, label="KSP", color="green")
axs[2].set_xlabel('Время, с')
axs[2].set_ylabel('Масса, кг')
axs[2].grid(True, linestyle='--', alpha=0.7)
axs[2].set_title('Масса ракеты, кг')
axs[2].legend()

plt.tight_layout()
plt.show()