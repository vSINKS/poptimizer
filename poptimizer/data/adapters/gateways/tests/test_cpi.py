"""Тесты для загрузки инфляции."""
import pandas as pd
import pytest

from poptimizer.data.adapters.gateways import cpi
from poptimizer.shared import col


@pytest.mark.asyncio
async def test_load_xlsx(mocker):
    """Парсинг Excel с необходимыми параметрами."""
    fake_read_excel = mocker.patch.object(cpi.pd, "read_excel")

    await cpi._load_xlsx(mocker.MagicMock())

    fake_read_excel.assert_called_once()

    _, kwargs = fake_read_excel.call_args
    assert kwargs == cpi.PARSING_PARAMETERS


VALID_CASES = (
    (
        pd.DataFrame([1]),
        "Таблица должна содержать 12 строк с месяцами",
    ),
    (
        pd.DataFrame(list(range(12)), columns=[1992]),
        "Первый год должен быть 1991",
    ),
    (
        pd.DataFrame(
            list(range(12)),
            columns=[1991],
            index=list(range(12)),
        ),
        "Первый месяц должен быть январь",
    ),
    (
        pd.DataFrame(
            list(range(12)),
            columns=[1991],
            index=["январь", *range(11)],
        ),
        None,
    ),
)


@pytest.mark.parametrize("df, msg", VALID_CASES)
def test_validate(df, msg):
    """Варианты ошибок в валидации исходного DataFrame с сайта."""
    if msg:
        with pytest.raises(cpi.CPIGatewayError, match=msg):
            cpi._validate(df)
    else:
        cpi._validate(df)


def test_clean_up():
    """Обработка исходного DataFrame с сайта."""
    df = pd.DataFrame(
        [[100, 200], [300, 400]],
        columns=[1992, 1993],
    )

    df_clean = cpi._clean_up(df)

    assert df_clean.values.tolist() == [
        [1.0],
        [3.0],
        [2.0],
        [4.0],
    ]
    assert df_clean.columns == [col.CPI]
    assert df_clean.index[0] == pd.Timestamp("1992-01-31")
    assert df_clean.index[-1] == pd.Timestamp("1992-04-30")


@pytest.mark.asyncio
async def test_loader(mocker):
    """Основной вариант работы загрузчика."""
    fake_session = mocker.MagicMock()
    fake_load_xlsx = mocker.patch.object(cpi, "_load_xlsx")
    fake_validate = mocker.patch.object(cpi, "_validate")
    fake_clean_up = mocker.patch.object(cpi, "_clean_up")

    loader = cpi.CPIGateway(fake_session)

    assert await loader.__call__() is fake_clean_up.return_value

    fake_load_xlsx.assert_called_once_with(fake_session)
    fake_validate.assert_called_once_with(fake_load_xlsx.return_value)
    fake_clean_up.assert_called_once_with(fake_load_xlsx.return_value)
