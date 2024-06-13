from testbook import testbook


@testbook("notebooks/01. IO/EarthRanger_IO.ipynb", execute=True)
def test_nb_er_io(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/01. IO/GEE_IO.ipynb", execute=True)
def test_nb_gee_io(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/01. IO/Landscape Dynamics Data.ipynb", execute=True)
def test_nb_ldd(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/02. Relocations & Trajectories/Relocations_and_Trajectories.ipynb", execute=True)
def test_nb_relocs_trajs(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/03. Home Range & Movescape/EcoGraph.ipynb", execute=True)
def test_nb_ecograph(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/03. Home Range & Movescape/Elliptical Time Density (ETD).ipynb", execute=True)
def test_nb_etd(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/03. Home Range & Movescape/Reduce Regions.ipynb", execute=True)
def test_nb_reduce(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/04. EcoMap & EcoPlot/EcoMap.ipynb", execute=True)
def test_nb_ecomap(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/04. EcoMap & EcoPlot/EcoPlot.ipynb", execute=True)
def test_nb_ecoplot(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/05. Environmental Analyses/Landscape Grid.ipynb", execute=True)
def test_nb_lg(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/05. Environmental Analyses/Remote Sensing Time Series Anomaly.ipynb", execute=True)
def test_nb_remote(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/05. Environmental Analyses/Seasonal Calculation.ipynb", execute=True)
def test_nb_seasonal(tb):
    # func = tb.get("func")
    print(tb)


@testbook("notebooks/06. Data Management/Tracking Data Gantt Chart.ipynb", execute=True)
def test_nb_tracking(tb):
    # func = tb.get("func")
    print(tb)
