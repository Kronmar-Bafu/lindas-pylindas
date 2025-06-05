from pylindas.pycube import Cube
import pandas as pd
import numpy as np
from time import time
import yaml
from multiprocessing import Pool, cpu_count, current_process
from rdflib import Graph


def prepare_data(num_obs, num_dim):
    data = np.random.random(size=(int(num_obs), num_dim))
    df = pd.DataFrame(data)
    df["Jahr"] = np.repeat(range(int(num_obs / 2)), 2)
    df["Station"] = np.tile([0, 1], reps=int(num_obs / 2))
    return df

def worker_job(args):
    data, cube_description, worker_id = args
    cube = Cube(dataframe=data, cube_yaml=cube_description, environment="TEST", local=True)
    cube.prepare_data()
    if worker_id == 0:
        cube.write_cube()
        cube.write_observations()
        cube.write_shape()
    else:
        cube.write_observations()

    cube.serialize(f"benchmarking/{worker_id}.ttl")

def merge_graphs(graphs):
    merged = Graph()
    for g in graphs:
        merged += g
    return merged


if __name__ == "__main__":
    times = []
    num_observations = [1e2, 1e3, 1e4, 1e5, 1e6]
    num_dimensions = [1,10]
    for num_obs in num_observations:
        for num_dim in num_dimensions:
            num_workers = cpu_count()

            df = prepare_data(num_obs, num_dim)

            tic = time()
            df_chunks = np.array_split(df, num_workers)

            with open(f"benchmarking/description_{num_dim}.yml", encoding="utf-8") as file:
                cube_description = yaml.safe_load(file)

            args_list = [(chunk, cube_description, i) for i, chunk in enumerate(df_chunks)]

            with Pool(processes=num_workers) as pool:
                pool.map(worker_job, args_list)
            print(f"Time for {num_obs} observations with {num_dim} dimensions and {num_workers} workers: {time() - tic}")
            times.append(time() - tic)

    df = pd.DataFrame({
        "Observations": np.repeat(num_observations, repeats=len(num_dimensions)),
        "Dimensions": np.tile(num_dimensions, reps=len(num_observations)),
        "Time": times
    })
    df.to_csv("benchmarking/results_no_validation_multiprocessing.csv", index=False)


