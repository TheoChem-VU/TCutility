if __name__ == "__main__":
    import os
    import glob

    if len(glob.glob("IRC*converged*.rkf")) > 0:
        if os.path.exists("TS.rkf"):
            os.remove("TS.rkf")

    for f in glob.glob("IRC*converged*.rkf"):
        os.remove(f)

    for f in glob.glob("t21*"):
        os.remove(f)

    for f in glob.glob("t12*"):
        os.remove(f)

    if os.path.exists("CreateAtoms.out"):
        os.remove("CreateAtoms.out")
