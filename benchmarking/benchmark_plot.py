import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pyplot import yscale

df_no_validation = pd.read_csv("benchmarking/results_no_validation.csv")
df_with_validation = pd.read_csv("benchmarking/results_with_validation.csv")

pal = {
    1: "plum",
    3: "fuchsia",
    5: "darkorchid",
    10: "indigo"
}

fig, ax =plt.subplots(1,2)
p1 = sns.barplot(x='Observations', y='Time', hue='Dimensions', data=df_no_validation, ax=ax[0], palette=pal)
p1.set(yscale='log')
p1.set_xticklabels(p1.get_xticklabels(), rotation=30)
p1.set_yticks([0.001,0.01, 0.1, 1, 10, 100, 1000])
p2 = sns.barplot(x='Observations', y='Time', hue='Dimensions', data=df_with_validation, ax=ax[1], palette=pal)
p2.set(yscale='log')
p2.set_xticklabels([10, 100, 1000, 10000, 100000, 1000000], rotation=30)
p2.set_yticks([0.001, 0.01, 0.1, 1, 10, 100, 1000])
handles, labels = plt.gca().get_legend_handles_labels()
fig.legend(handles, labels, loc='right', title="Dimensions")
ax[0].set_title("No validation")
ax[1].set_title("With validation")
ax[0].spines['top'].set_visible(False)
ax[0].spines['right'].set_visible(False)
ax[0].get_legend().remove()
ax[1].get_legend().remove()
ax[1].spines['top'].set_visible(False)
ax[1].spines['right'].set_visible(False)

fig.tight_layout()
plt.show()