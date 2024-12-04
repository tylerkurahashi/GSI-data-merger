# GSI-data-merger

## Usage

0. `docker compose up -d` and then choose `attach to a executing container` with VScode extension `ms-vscode-remote.vscode-remote-extensionpack`

1. Place all your zipfiles downloaded from `https://fgd.gsi.go.jp/download/mapGis.php` in `./data/zips`

2. (Optional) If you want to filter polygons within an area, prepare a polygon file which specifies its area and place it in `./data/filter`, and also specify its path in `FILTER_POLYGON_PATH` defined in `const.py`

3. Excecute `python3 main.py` in the root directory of this repository.

4. Check your output in `./data/output`

## Caution

- Currently only for "BldA" type polygons.

- Merging numbers of file consumes much time. (I will try to optimize when I feel to do so.)</br>
(174 files took around an hour)