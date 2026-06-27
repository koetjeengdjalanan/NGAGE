"""Data-processing pipelines for network device bandwidth, CPU, memory, and logs.

Provide pure-function processors that merge raw Grafana CSV exports
against Excel lookup tables to compute capacity utilisation percentages
and availability occurrence counts for various device categories
(branch routers, enterprise, F5 load balancers, firewalls, etc.).
"""

import math

import pandas as pd


def bw_unit_normalize(input):
    """Normalize a bandwidth record's value to megabits per second.

    Convert the ``Bandwidth`` field in-place from its original unit
    (bps, kbps, Mbps, Gbps, or their ``/s`` equivalents) to Mbps by
    multiplying by the appropriate power of ten, then set ``Unit`` to
    ``"Mbps"``.

    Note:
        This function **mutates** the input record in-place.

    Args:
        input (dict | pd.Series): A record containing ``Bandwidth``
            (numeric) and ``Unit`` (str) fields.

    Returns:
        dict | pd.Series: The same record with ``Bandwidth`` converted
            to Mbps and ``Unit`` set to ``"Mbps"``.
    """
    units = {
        "bps": -6,
        "kbps": -3,
        "mbps": 0,
        "gbps": 3,
        "b/s": -6,
        "kb/s": -3,
        "mb/s": 0,
        "gb/s": 3,
    }
    input["Bandwidth"] = input["Bandwidth"] * math.pow(10, units[input["Unit"].strip().lower()])
    input["Unit"] = "Mbps"
    return input


def process_with_from_n_to(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Merge bandwidth data using From/To hostname-interface pairs.

    For each metric in ``raw``, first attempt a left-join against the
    lookup table on the *From* hostname and interface columns. For any
    rows that remain unmatched (``NaN`` bandwidth), fall back to a
    second join on the *To* columns. Finally, compute a utilisation
    percentage for each metric and merge all metrics into a single
    result DataFrame.

    Args:
        raw (dict[str, pd.DataFrame]): Mapping of metric names
            (e.g. ``"bw-in"``, ``"bw-out"``) to DataFrames, each
            containing ``Hostname``, ``Interface``, ``Bandwidth``, and
            ``Unit`` columns.
        lookUpTable (pd.DataFrame): Lookup table with ``From Hostname``,
            ``From Interface``, ``To Hostname``, ``To Interface``, and
            ``Bandwidth`` columns describing network links.

    Returns:
        pd.DataFrame: A single DataFrame containing all lookup-table
            columns plus per-metric bandwidth and percentage columns.
    """
    calc: dict[str, pd.DataFrame] = {}
    for each in list(raw.keys()):
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["From Hostname", "From Interface"],
            right_on=["Hostname", "Interface"],
        ).drop(["Hostname", "Interface"], axis=1)
        missing = calc[each][calc[each][f"{each} Bandwidth"].isna()]
        if not missing.empty:
            additional = pd.merge(
                left=lookUpTable,
                right=raw[each],
                how="left",
                left_on=["To Hostname", "To Interface"],
                right_on=["Hostname", "Interface"],
            ).drop(["Hostname", "Interface"], axis=1)
            calc[each].update(additional)
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    return res


def process_basic(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Merge bandwidth data using simple hostname-interface matching.

    Unlike ``process_with_from_n_to``, this function joins raw metrics
    directly on ``Hostname`` and ``Interface`` without a From/To
    fallback. Compute a utilisation percentage for each metric and merge
    all metrics into a single result DataFrame.

    Args:
        raw (dict[str, pd.DataFrame]): Mapping of metric names to
            DataFrames, each with ``Hostname``, ``Interface``,
            ``Bandwidth``, and ``Unit`` columns.
        lookUpTable (pd.DataFrame): Lookup table with ``Hostname``,
            ``Interface``, and ``Bandwidth`` columns.

    Returns:
        pd.DataFrame: A single DataFrame containing all lookup-table
            columns plus per-metric bandwidth and percentage columns.
    """
    calc: dict[str, pd.DataFrame] = {}
    for each in list(raw.keys()):
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        raw[each]["Interface"] = raw[each]["Interface"].apply(lambda x: str(x))
        lookUpTable["Interface"] = lookUpTable["Interface"].apply(lambda x: str(x))
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["Hostname", "Interface"],
            right_on=["Hostname", "Interface"],
        )
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    return res


def process_f5(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Process F5 load-balancer bandwidth, CPU, and memory metrics.

    Merge inbound and outbound bandwidth data against the lookup table,
    pivot per-CPU utilisation percentages from the PDC and SDC CPU
    exports, and join memory utilisation. The resulting DataFrame is
    reindexed into a fixed column order with ``F5``, ``Hostname``,
    eight CPU columns, ``mem %``, interface bandwidth, and percentage
    columns.

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary containing keys
            ``"bw-in"``, ``"bw-out"``, ``"pdc-cpu"``, ``"sdc-cpu"``,
            and ``"mem"`` mapping to their respective DataFrames.
        lookUpTable (pd.DataFrame): F5 lookup table with ``Hostname``,
            ``Interface``, and ``Bandwidth`` columns.

    Returns:
        pd.DataFrame: A consolidated DataFrame with bandwidth
            percentages, per-CPU utilisation, and memory utilisation
            for each F5 host.
    """
    calc: dict[str, pd.DataFrame] = {}
    for each in ["bw-in", "bw-out"]:
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        raw[each]["Interface"] = raw[each]["Interface"].apply(lambda x: str(x))
        lookUpTable["Interface"] = lookUpTable["Interface"].apply(lambda x: str(x))
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["Hostname", "Interface"],
            right_on=["Hostname", "Interface"],
        )
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    rawCpu = pd.concat([raw["pdc-cpu"], raw["sdc-cpu"]]).reset_index()
    rawCpu["Hostname"] = rawCpu["Metric"].apply(lambda x: x.split(" ")[0].lower())
    rawCpu["cpu_num"] = rawCpu["Metric"].apply(lambda x: "cpu" + x.split("cpu")[-1])
    rawCpu = rawCpu.pivot_table(index="Hostname", columns="cpu_num", values="95th CPU", aggfunc="first").reset_index()
    cpu_columns = [f"cpu{i}" for i in range(8)]
    rawCpu[cpu_columns] = rawCpu[cpu_columns].map(lambda x: float(str(x).split("%")[0]) / 100)
    res = pd.merge(res, rawCpu, how="left", on="Hostname")
    raw["mem"].rename(columns={"Metric": "Hostname", "95th Memory": "mem %"}, inplace=True)
    raw["mem"]["mem %"] = raw["mem"]["mem %"].apply(lambda x: float(str(x).split("%")[0]) / 100)
    res = pd.merge(res, raw["mem"], how="left", on="Hostname")
    colOrder = (
        [
            "F5",
            "Hostname",
        ]
        + [f"cpu{i}" for i in range(8)]
        + [
            "mem %",
            "Interface",
            "Bandwidth",
            "bw-in Bandwidth",
            "bw-in %",
            "bw-out Bandwidth",
            "bw-out %",
        ]
    )
    res = res.reindex(columns=colOrder)
    return res


def process_firewall(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Process firewall CPU, memory, and connection-count metrics.

    Concatenate checkpoint (``con-cp``) and non-checkpoint (``con-noncp``)
    connection-count DataFrames, then left-join each metric category
    against the lookup table. Percentage strings (e.g. ``"85.3%"``) are
    parsed and converted to decimal floats.

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary containing keys
            ``"cpu"``, ``"mem"``, ``"con-cp"``, and ``"con-noncp"``
            mapping to their respective DataFrames.
        lookUpTable (pd.DataFrame): Firewall lookup table with a
            ``Hostname`` column.

    Returns:
        pd.DataFrame: The lookup table augmented with ``CPU 95%``,
            ``Memory 95%``, and ``Connection Count 95%`` columns as
            decimal floats.
    """
    raw["con"] = pd.concat([raw["con-cp"], raw["con-noncp"]]).reset_index()
    del raw["con-cp"], raw["con-noncp"]
    for each in raw.keys():
        lookUpTable = pd.merge(lookUpTable, raw[each], how="left", on="Hostname")
    for col in ["CPU 95%", "Memory 95%", "Connection Count 95%"]:
        lookUpTable[col] = lookUpTable[col].apply(lambda x: (float(str(x).split("%")[0].replace(",", ".")) / 100))
    lookUpTable.drop("index", axis=1, inplace=True)
    return lookUpTable


def conc_df(orig: dict[str, pd.DataFrame], ext: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Concatenate two identically-keyed dictionaries of DataFrames.

    For each key present in ``orig``, vertically concatenate
    ``orig[key]`` and ``ext[key]`` with ``ignore_index=True``.

    Args:
        orig (dict[str, pd.DataFrame]): Primary dictionary of
            DataFrames.
        ext (dict[str, pd.DataFrame]): Extension dictionary whose
            DataFrames are appended to the corresponding ``orig``
            entries.

    Returns:
        dict[str, pd.DataFrame]: New dictionary with the concatenated
            DataFrames.
    """
    res = {}
    for key in orig.keys():
        res[key] = pd.concat(objs=[orig[key], ext[key]], axis=0, ignore_index=True)
    return res


def count_occurrences(raw: pd.DataFrame, lookupTable: pd.DataFrame) -> pd.DataFrame:
    """Count interface-down events per hostname-interface pair.

    Build a regex pattern from the unique interfaces in ``lookupTable``,
    filter ``raw`` for log messages containing ``"changed state to
    down"``, extract the matching interface name, deduplicate by
    timestamp/hostname/interface, and group-count. The counts are
    left-joined back onto ``lookupTable``.

    Args:
        raw (pd.DataFrame): Raw syslog DataFrame with ``log_message``,
            ``@timestamp``, and ``hostname`` columns.
        lookupTable (pd.DataFrame): Lookup table with ``Headend Router``
            and ``Interface`` columns.

    Returns:
        pd.DataFrame: The lookup table with an added ``Count`` column
            (integer, zero-filled for interfaces with no events).
    """
    interface_patterns = "|".join(lookupTable["Interface"].unique().astype(str))
    raw = (
        raw[raw["log_message"].str.contains("changed state to down", case=False)]
        .assign(Interface=raw["log_message"].str.extract(f"({interface_patterns})"))
        .drop_duplicates(subset=["@timestamp", "hostname", "Interface"], keep="last")
    )
    count_series = raw.groupby(["hostname", "Interface"]).size().reset_index(name="Count")
    count_series.columns = [col.title() for col in count_series.columns]
    res = (
        pd.merge(
            left=lookupTable,
            right=count_series,
            left_on=["Headend Router", "Interface"],
            right_on=["Hostname", "Interface"],
            how="left",
        )
        .drop(columns="Hostname")
        .fillna({"Count": 0})
        .astype({"Count": int})
    )
    return res


def count_by_column(lookupTable: pd.DataFrame, columnList: list[str], raw: pd.DataFrame) -> pd.DataFrame:
    """Count interface-down events grouped by specific hostname columns.

    Similar to ``count_occurrences`` but produces one count column per
    hostname in ``columnList``. For each hostname, filter the grouped
    counts, merge onto the lookup table, and rename the ``Count``
    column to the hostname.

    Args:
        lookupTable (pd.DataFrame): Lookup table with an ``Interface``
            column.
        columnList (list[str]): Hostnames to count separately. Each
            hostname becomes its own integer column in the result.
        raw (pd.DataFrame): Raw syslog DataFrame with ``log_message``,
            ``@timestamp``, and ``hostname`` columns.

    Returns:
        pd.DataFrame: The lookup table with one integer count column
            per hostname in ``columnList``.
    """
    res = lookupTable.copy()
    interface_patterns = "|".join(lookupTable["Interface"].unique().astype(str))
    raw = (
        raw[raw["log_message"].str.contains("changed state to down", case=False)]
        .assign(Interface=raw["log_message"].str.extract(f"({interface_patterns})"))
        .drop_duplicates(subset=["@timestamp", "hostname", "Interface"], keep="last")
    )
    count_series = raw.groupby(["hostname", "Interface"]).size().reset_index(name="Count")
    for column in columnList:
        res = (
            res.merge(
                count_series[count_series["hostname"] == column],
                left_on="Interface",
                right_on="Interface",
                how="left",
            )
            .drop(columns=["hostname"])
            .fillna({"Count": 0})
            .astype({"Count": int})
            .rename(columns={"Count": column})
        )
    return res
