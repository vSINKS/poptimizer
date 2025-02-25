"""Реализация последовательных тестов.

Используются результаты из следующих работ:

Time-uniform, nonparametric, nonasymptotic confidence sequences
https://arxiv.org/abs/1810.08240
Sequential estimation of quantiles with applications to A/B-testing and best-arm identification
https://arxiv.org/abs/1906.09712
"""
import itertools

import numpy as np
from scipy import special, stats


def _median_conf_radius(
    t: int,  # noqa: WPS111
    alfa: float,
    m: int = 1,  # noqa: WPS111
    nu: float = 2.04,
    s: float = 1.4,  # noqa: WPS111
) -> float:
    """Отклонение выборочной медиана от фактического значения при проведении последовательных тестов.

    Данная функция реализует расчет сужающейся последовательности доверительных интервалов для
    выборочной медианы равномерно корректных по времени тестирования. И базируется на формулах (41) -
    (44), адаптированных для медианы (p=0.5) из работы:

    Sequential estimation of quantiles with applications to A/B-testing and best-arm identification
    https://arxiv.org/abs/1906.09712

    В качестве базовых значений параметров взяты значения из формулы (1). Параметр m отвечает за
    период начала тестирования, а параметры nu и s регулируют форму изменения интервалов по времени и
    могут быть подобраны для минимизации интервала для целевого значения времени t.

    Классические тесты на сравнения двух выборок предполагают выбор до начала эксперимента размеров
    выборок и последующего единственного тестирования гипотезы для заданных размеров выборок.

    Часто до начала эксперимента сложно установить необходимый размер выборки. Однако если будет
    осуществляться процедура постепенного увеличения выборки и расчета p-value на каждом шаге до
    достижения критического значения фактическое критическое значение будет существенно завышено. Более
    того закон повторного логарифма гарантирует, что любой уровень значимости из классических тестов
    рано или поздно будет пробит с вероятностью 1.

    При проведении последовательного сравнения так же нельзя воспользоваться классическими методами
    коррекции на множественное тестирования, так как они предполагают слабую зависимость между
    гипотезами. В случае последовательного тестирования гипотеза для момента времени t очень сильно
    связана с гипотезой для момента времени t+1, поэтому обычные корректировки будут слишком
    консервативными.

    :param t:
        Номер интервала для которого осуществляется процедура последовательного тестирования. Тесты
        начинаются с момента времени t >= n и осуществляются последовательно для каждого t.
    :param alfa:
        Значение p-value для процедуры последовательного тестирования. Вероятность пробить
        последовательность доверительных интервалов при тестировании для всех t >= n меньше alfa.
    :param m:
        Период с которого начинается непрерывный анализ выборочной медианы. Должен быть больше или
        равен 1. Значение t >= n.
    :param nu:
        Параметр регулирующий форму убывания радиуса с ростом количества проверок. Должен быть строго
        больше 1. Рекомендуемое значение 2.04 в первой формуле на первой странице.
    :param s:
        Параметр регулирующий форму убывания радиуса с ростом количества проверок. Должен быть строго
        больше 1. Рекомендуемое значение 1.4 в первой формуле на первой странице.
    :return:
        Радиус доверительного интервала для медианы.
    """
    k1 = ((nu ** 0.25) + (nu ** -0.25)) / (2 ** 0.5)  # noqa: WPS432

    iterated_logarithm = nu * t / m
    iterated_logarithm = s * np.log(np.log(iterated_logarithm))

    sequential_probability_ratio = alfa * np.log(nu) ** s
    sequential_probability_ratio = np.log(2 * special.zeta(s) / sequential_probability_ratio)

    l_t = iterated_logarithm + sequential_probability_ratio

    return k1 * 0.5 * (l_t / t) ** 0.5


def minimum_bounding_n(alfa: float) -> int:
    """Подбор минимального ограничивающего n для заданного уровня значимости.

    Параметр n в формуле доверительных интервалов при последовательном тестировании отвечает за момент
    начала тестов. Однако для малых n интервалы имеют ширину больше 0.5, то есть не накладывают
    никаких ограничений на медиану, поэтому n может быть увеличено.

    Данная функция подбирает значение n, так чтобы при n = t интервалы накладывали хотя бы минимальное
    ограничение на величину медианы, то есть расчетный доверительный радиус был бы меньше 0.5.
    """
    for n in itertools.count(1):  # noqa: WPS111
        if _median_conf_radius(n, alfa, n) < 0.5:  # noqa: WPS459
            return n


def median_conf_bound(sample: list[float], p_value: float) -> tuple[float, float]:
    """Доверительный интервал для медианы.

    Используются значения по умолчанию для nu и s, а величина n подбирается под ограничивающие
    интервалы с начала тестирования под заданное p_value.
    """
    t = len(sample)  # noqa: WPS111
    n = minimum_bounding_n(p_value)  # noqa: WPS111
    if t < n:
        return -np.inf, np.inf
    radius = _median_conf_radius(t, p_value, n)

    return tuple(
        stats.scoreatpercentile(
            sample,
            [(0.5 - radius) * 100, (0.5 + radius) * 100],
        ),
    )
