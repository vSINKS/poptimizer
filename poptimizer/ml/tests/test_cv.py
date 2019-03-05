import hyperopt
import pandas as pd
import pytest
from hyperopt import hp
from hyperopt.pyll import Apply

from poptimizer.config import POptimizerError
from poptimizer.ml import cv_old, examples_old
from poptimizer.ml.feature_old import YEAR_IN_TRADING_DAYS, divyield_old
from poptimizer.portfolio import portfolio

PARAMS = (
    (
        (True, {"days": 21}),
        (True, {"days": 252}),
        (True, {}),
        (True, {"days": 252}),
        (True, {"days": 252}),
    ),
    {
        "bagging_temperature": 1,
        "depth": 6,
        "ignored_features": (),
        "l2_leaf_reg": 3,
        "learning_rate": 0.1,
        "one_hot_max_size": 2,
        "random_strength": 1,
    },
)


def test_log_space():
    space = cv_old.log_space("test1", [2, 8])
    assert isinstance(space, Apply)
    assert "test1" in str(space)
    assert "loguniform" in str(space)
    assert "0.693147" in str(space)
    assert "2.079441" in str(space)


def test_get_model_space():
    space = cv_old.get_model_space()
    assert isinstance(space, dict)
    assert len(space) == 6

    assert isinstance(space["one_hot_max_size"], Apply)
    assert "switch" in str(space["one_hot_max_size"])
    assert "Literal{2}" in str(space["one_hot_max_size"])
    assert "Literal{100}" in str(space["one_hot_max_size"])

    assert isinstance(space["learning_rate"], Apply)
    assert "loguniform" in str(space["learning_rate"])

    assert isinstance(space["depth"], Apply)
    assert "switch" in str(space["depth"])
    assert f"{{{cv_old.MAX_DEPTH}}}" in str(space["depth"])

    assert isinstance(space["l2_leaf_reg"], Apply)
    assert "loguniform" in str(space["l2_leaf_reg"])

    assert isinstance(space["random_strength"], Apply)
    assert "loguniform" in str(space["random_strength"])

    assert isinstance(space["bagging_temperature"], Apply)
    assert "loguniform" in str(space["bagging_temperature"])


def test_float_bounds_check_middle(capsys):
    cv_old.float_bounds_check("qwerty", 15, [10, 20])
    captured = capsys.readouterr()
    assert captured.out == ""


def test_float_bounds_check_lower(capsys):
    cv_old.float_bounds_check("qwerty", 10.5, [10, 20])
    captured = capsys.readouterr()
    assert "qwerty" in captured.out
    assert "20" in captured.out
    assert "8.8e+00" in captured.out


def test_float_bounds_check_upper(capsys):
    cv_old.float_bounds_check("qwerty", 19.5, [10, 20])
    captured = capsys.readouterr()
    assert "qwerty" in captured.out
    assert "10" in captured.out
    assert "2.3e+01" in captured.out


def test_check_model_bounds_middle(capsys):
    params = dict(
        learning_rate=sum(cv_old.LEARNING_RATE) / 2,
        l2_leaf_reg=sum(cv_old.L2_LEAF_REG) / 2,
        random_strength=sum(cv_old.RANDOM_STRENGTH) / 2,
        bagging_temperature=sum(cv_old.BAGGING_TEMPERATURE) / 2,
        depth=int(cv_old.MAX_DEPTH / 2),
    )
    cv_old.check_model_bounds(params)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_check_model_bounds_lower(capsys):
    params = dict(
        learning_rate=min(cv_old.LEARNING_RATE) * 1.05,
        l2_leaf_reg=min(cv_old.L2_LEAF_REG) * 1.05,
        random_strength=min(cv_old.RANDOM_STRENGTH) * 1.05,
        bagging_temperature=min(cv_old.BAGGING_TEMPERATURE) * 1.05,
        depth=0,
    )
    cv_old.check_model_bounds(params)
    captured = capsys.readouterr()
    assert "learning_rate" in captured.out
    assert "l2_leaf_reg" in captured.out
    assert "random_strength" in captured.out
    assert "bagging_temperature" in captured.out


def test_check_model_bounds_upper(capsys):
    params = dict(
        learning_rate=max(cv_old.LEARNING_RATE) / 1.05,
        l2_leaf_reg=max(cv_old.L2_LEAF_REG) / 1.05,
        random_strength=max(cv_old.RANDOM_STRENGTH) / 1.05,
        bagging_temperature=max(cv_old.BAGGING_TEMPERATURE) / 1.05,
        depth=cv_old.MAX_DEPTH,
    )
    cv_old.check_model_bounds(params)
    captured = capsys.readouterr()
    assert "learning_rate" in captured.out
    assert "l2_leaf_reg" in captured.out
    assert "random_strength" in captured.out
    assert "bagging_temperature" in captured.out

    assert "MAX_DEPTH" in captured.out
    assert str(cv_old.MAX_DEPTH + 1) in captured.out


def test_make_model_params():
    data_params = (
        (False, {"days": 49}),
        (False, {"days": 235}),
        (True, {}),
        (False, {"days": 252}),
        (True, {"days": 252}),
    )
    model_params = {
        "bagging_temperature": 1,
        "depth": 6,
        "l2_leaf_reg": 3,
        "learning_rate": 4,
        "one_hot_max_size": 2,
        "random_strength": 5,
        "ignored_features": [2, 4],
    }
    result = cv_old.make_model_params(data_params, model_params)
    assert isinstance(result, dict)
    assert len(result) == 12
    assert result["bagging_temperature"] == 1
    assert result["depth"] == 6
    assert result["l2_leaf_reg"] == 3
    assert result["learning_rate"] == 4
    assert result["one_hot_max_size"] == 2
    assert result["random_strength"] == 5
    assert result["ignored_features"] == [0, 2]

    assert result["iterations"] == cv_old.MAX_ITERATIONS
    assert result["random_state"] == cv_old.SEED
    assert result["od_type"] == "Iter"
    assert result["verbose"] is False
    assert result["allow_writing_files"] is False


def test_cv_model():
    data = examples_old.Examples(("LSNGP", "LKOH", "GMKN"), pd.Timestamp("2018-12-14"))
    result = cv_old.cv_model(PARAMS, data)

    assert isinstance(result, dict)
    assert len(result) == 5
    assert result["loss"] == pytest.approx(0.959_348_206_025_903_5 ** 2 - 1)
    assert result["status"] == "ok"
    assert result["std"] == pytest.approx(
        3.251_270_743_258_923 / YEAR_IN_TRADING_DAYS ** 0.5
    )
    assert result["r2"] == pytest.approx(0.079_651_019_594_880_52)
    data_params, model_params = result["params"]
    assert data_params == PARAMS[0]
    for key, value in PARAMS[1].items():
        assert model_params[key] == value
    for key, value in cv_old.TECH_PARAMS.items():
        if key == "iterations":
            assert model_params[key] < value
        else:
            assert model_params[key] == value


def test_cv_model_raise_max_iter():
    PARAMS[1]["learning_rate"] = 0.001
    data = examples_old.Examples(("LSNGP", "LKOH", "GMKN"), pd.Timestamp("2018-12-14"))
    with pytest.raises(POptimizerError) as error:
        cv_old.cv_model(PARAMS, data)
    assert "Необходимо увеличить MAX_ITERATIONS =" in str(error.value)


def test_cv_all_features_false():
    data = examples_old.Examples(("LSNGP", "LKOH", "MSTT"), pd.Timestamp("2018-12-20"))
    params = (
        (
            (True, {"days": 21}),
            (False, {"days": 252}),
            (False, {}),
            (False, {"days": 252}),
            (False, {"days": 252}),
        ),
        {
            "bagging_temperature": 1,
            "depth": 6,
            "ignored_features": (),
            "l2_leaf_reg": 3,
            "learning_rate": 0.1,
            "one_hot_max_size": 2,
            "random_strength": 1,
        },
    )
    result = cv_old.cv_model(params, data)
    assert result == dict(
        loss=None, status=hyperopt.STATUS_FAIL, std=None, r2=None, params=None
    )


def test_optimize_hyper(monkeypatch, capsys):
    space = (
        (
            (True, {"days": hp.choice("label", list(range(21, 31)))}),
            (True, {"days": 186}),
            (False, {}),
            (True, {"days": 279}),
            (True, {"days": 252}),
        ),
        {
            "bagging_temperature": 1,
            "depth": 6,
            "l2_leaf_reg": 3,
            "learning_rate": 0.1,
            "one_hot_max_size": 2,
            "random_strength": 1,
            "ignored_features": [],
        },
    )
    cases = examples_old.Examples(("LSNGP", "LKOH", "GMKN"), pd.Timestamp("2018-12-14"))
    monkeypatch.setattr(cv_old, "MAX_SEARCHES", 10)
    monkeypatch.setattr(cases, "get_params_space", lambda: space[0])
    monkeypatch.setattr(cv_old, "get_model_space", lambda: space[1])

    result = cv_old.optimize_hyper(cases)

    captured = capsys.readouterr()
    assert "Необходимо расширить" in captured.out

    assert isinstance(result, tuple)
    assert result[0] == (
        (True, {"days": 30}),
        (True, {"days": 186}),
        (False, {}),
        (True, {"days": 279}),
        (True, {"days": 252}),
    )
    model_params = {
        "bagging_temperature": 1,
        "depth": 6,
        "l2_leaf_reg": 3,
        "learning_rate": 0.1,
        "one_hot_max_size": 2,
        "random_strength": 1,
    }
    for k, v in model_params.items():
        assert result[1][k] == pytest.approx(v)


def test_find_better_model(monkeypatch, capsys):
    monkeypatch.setattr(cv_old, "MAX_SEARCHES", 10)
    monkeypatch.setattr(cv_old, "MAX_DEPTH", 7)
    monkeypatch.setattr(divyield_old.DivYield, "RANGE", [280, 398])
    pos = dict(LSNGP=10, KZOS=20, GMKN=30)
    port = portfolio.Portfolio(pd.Timestamp("2018-12-19"), 100, pos)
    cv_old.find_better_model(port)
    captured = capsys.readouterr()
    assert "Базовая модель" in captured.out
    assert "Найденная модель" in captured.out
    assert "ЛУЧШАЯ МОДЕЛЬ - Найденная модель" in captured.out


def test_find_better_model_fake_base(monkeypatch, capsys):
    monkeypatch.setattr(cv_old, "MAX_SEARCHES", 10)
    monkeypatch.setattr(
        cv_old, "print_result", lambda x, y, z: 1 if x == "Базовая модель" else 0
    )
    pos = dict(LSNGP=10, KZOS=20, GMKN=30)
    port = portfolio.Portfolio(pd.Timestamp("2018-12-19"), 100, pos)
    cv_old.find_better_model(port)
    captured = capsys.readouterr()
    assert "ЛУЧШАЯ МОДЕЛЬ - Базовая модель" in captured.out
