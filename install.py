import pathlib


if __name__ == "__main__":
    moneydance_dir = pathlib.Path(
        "~/Library/Containers/com.infinitekind.MoneydanceOSX"
        "/Data/Library/Application Support/Moneydance"
    ).expanduser()
    here = pathlib.Path(__file__).parent
    lib = moneydance_dir.joinpath("python", "Lib")
    lib.symlink_to(here)
