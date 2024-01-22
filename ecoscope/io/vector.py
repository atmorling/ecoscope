import os
from shutil import which
from subprocess import Popen, PIPE


def export_pmtiles(gdf, filepath, layer_name="", use_gdal=False, *args):

    tempfile = "temp.fgb"
    gdf.to_file(tempfile, "FlatGeobuf")
    filepath = filepath

    if (cmd := which("tippecanoe")) and not use_gdal:
        if len(args) == 0:
            args = [cmd, "-zg", "-o", filepath, "--drop-densest-as-needed", "--extend-zooms-if-still-dropping"]
            if layer_name != "":
                args.extend(["-l", layer_name])
            args.extend([tempfile])
        else:
            args = [cmd] + args + ["-o", filepath, tempfile]

    elif cmd := which("ogr2ogr"):
        args = [cmd, "-progress", "-f", "PMTiles", "-dsco", "MAXZOOM=20"]
        if layer_name != "":
            args.extend(["-lco", "NAME=" + layer_name])
        args.extend([filepath, tempfile])

    else:
        raise FileNotFoundError("ogr2ogr was not found on path")

    with Popen(args, stdout=PIPE) as proc:
        while proc.poll() is None:
            print(proc.stdout.read1().decode("utf-8"), end="", flush=True)

    os.remove(tempfile)

    return filepath
