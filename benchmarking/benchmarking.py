import pandas as pd
import numpy as np
from time import time
from pylindas.pycube import Cube
import yaml


def benchmark(num_obs, num_dim, validate):
    data = np.random.random(size=(int(num_obs), num_dim))
    df = pd.DataFrame(data)
    df["Jahr"] = np.repeat(range(int(num_obs/2)),2)
    df["Station"] = np.tile([0,1],reps=int(num_obs/2))

    with open(f"benchmarking/description_{num_dim}.yml", encoding="utf-8") as file:
        cube_description = yaml.safe_load(file)

    tic = time()
    cube = Cube(dataframe=df, cube_yaml=cube_description, environment="TEST", local=True)
    cube.prepare_data()
    cube.write_cube()
    cube.write_observations()
    cube.write_shape()
    if validate:
        valid, text = cube.validate()

    del cube
    return time()-tic


if __name__ == "__main__":
    times = []
    num_observations_with_validation = [1e1, 1e2, 1e3, 1e4]
    num_observations_no_validation = [1e1, 1e2, 1e3, 1e4, 1e5, 1e6]
    num_dimensions = [1, 3, 5, 10]
    for num_obs in num_observations_no_validation:
        for num_dim in num_dimensions:
            times.append(benchmark(num_obs, num_dim, validate=False))


    times = []
    for num_obs in num_observations_with_validation:
        for num_dim in num_dimensions:
            times.append(benchmark(num_obs, num_dim, validate=True))

    df = pd.DataFrame(
        {
            "Observations": np.repeat(num_observations_with_validation, repeats=len(num_dimensions)),
            "Dimensions": np.tile(num_dimensions, reps=len(num_observations_with_validation)),
            "Time": times
        }
    )
    df.to_csv("benchmarking/results_with_validation.csv", index=False)
