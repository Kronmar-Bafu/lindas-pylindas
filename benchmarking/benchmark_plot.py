import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pyplot import yscale

pal = {
    "Single Core": "cyan",
    "Multi Core": "darkslategray"
}


def plot_benchmark(df, fig_title, file_path):
    fig, ax =plt.subplots(1,2)

    p1 = sns.barplot(x='Observations', y='Time', hue='Method', data=df[df["Dimensions"]==1], ax=ax[0], palette=pal)
    p1.set(yscale='log')
    p1.set_xticklabels(p1.get_xticklabels(), rotation=30)
    p1.set_yticks([0.01, 0.1, 1, 10, 100, 1000])

    p2 = sns.barplot(x="Observations", y="Time", hue="Method", data=df[df["Dimensions"]==10], ax=ax[1], palette=pal)
    p2.set(yscale="log")
    p2.set_xticklabels(p2.get_xticklabels(), rotation=30)
    p2.set_yticks([ 0.01, 0.1, 1, 10, 100, 1000])

    handles, labels = plt.gca().get_legend_handles_labels()
    fig.legend(handles, labels, loc='right', title="Method", bbox_to_anchor=(1.0,0.5), fontsize="small")
    fig.suptitle(fig_title)

    ax[0].set_title("1 Measurement")
    ax[1].set_title("10 Measurements")
    ax[0].spines['top'].set_visible(False)
    ax[0].spines['right'].set_visible(False)
    ax[0].set_ylabel("Time [s]")
    ax[0].get_legend().remove()
    ax[1].spines['top'].set_visible(False)
    ax[1].spines['right'].set_visible(False)
    ax[1].set_ylabel("Time [s]")
    ax[1].get_legend().remove()

    fig.tight_layout()
    plt.subplots_adjust(right=0.8)
    plt.savefig(file_path, format="png")

if __name__ == "__main__":
    df_no_validation = pd.read_csv("benchmarking/results_no_validation.csv")
    df_no_validation["Method"] = "Single Core"
    df_with_validation = pd.read_csv("benchmarking/results_with_validation.csv")
    df_with_validation["Method"] = "Single Core"
    df_no_validation_multiprocess = pd.read_csv("benchmarking/results_no_validation_multiprocessing.csv")
    df_no_validation_multiprocess["Method"] = "Multi Core"
    df_with_validation_multiprocess = pd.read_csv("benchmarking/results_with_validation_multiprocessing.csv")
    df_with_validation_multiprocess["Method"] = "Multi Core"

    df_no_validation = pd.concat([df_no_validation, df_no_validation_multiprocess], ignore_index=True)
    df_with_validation = pd.concat([df_with_validation, df_with_validation_multiprocess], ignore_index=True)

    plot_benchmark(df_no_validation, "No Validation", "benchmarking/no_validation.png")
    plot_benchmark(df_with_validation, "With Validation", "benchmarking/with_validation.png")
# p2 = sns.barplot(x='Observations', y='Time', hue='Dimensions', data=df_with_validation, ax=ax[1], palette=pal)
# p2.set(yscale='log')
# p2.set_xticklabels([100, 1000, 10000, 100000, 1000000], rotation=30)
# p2.set_yticks([ 0.01, 0.1, 1, 10, 100, 1000])


#
# p4 = sns.barplot(x="Observations", y="Time", hue="Dimensions", data=df_with_validation_multiprocess, ax=ax[1,1], palette=pal)
# p4.set(yscale="log")
# p4.set_xticklabels(p4.get_xticklabels(), rotation=30)
# p4.set_yticks([ 0.01, 0.1, 1, 10, 100, 1000])


# ax[1].get_legend().remove()
# ax[1].spines['top'].set_visible(False)
# ax[1].spines['right'].set_visible(False)
# ax[1,0].get_legend().remove()
# ax[1,0].spines['top'].set_visible(False)
# ax[1,0].spines['right'].set_visible(False)

