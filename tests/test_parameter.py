import requests, pandas as pd, numpy as np, os, matplotlib.pyplot as plt
import re, time, json
from collections import Counter
import seaborn as sns

from pprint import pprint

def get_rootdir() -> str:
    cwd = os.path.abspath(os.getcwd())
    end = re.search(r'hfms-backend', cwd).end()
    rootdir = cwd[:end]

    return rootdir

if __name__ == '__main__':
    start_all_process = time.time()
    version = 3
    base_path = get_rootdir()
    data_path = os.path.join(base_path, 'tests/test_data/')

    data = pd.read_csv(os.path.join(data_path, 'positive_case.csv' if case=='positive' else 'negative_case.csv'))

    try:
        data = data.set_index('SEQN', drop=True)
        data['Quest16_MCQ160B'] = data['Quest16_MCQ160B'].astype(int)
    except Exception as error:
        print("Error", error)

    sampling_data = data.sample(n=1, random_state=43)

    generations = np.arange(1, 101)
    accuracy_1 = 0.5 + 0.005 * generations
    accuracy_2 = 0.6 + 0.004 * generations
    accuracy_3 = 0.7 + 0.003 * generations

    plt.plot(generations, accuracy_1, label='Mutation Rate 0.01')
    plt.plot(generations, accuracy_2, label='Mutation Rate 0.05')
    plt.plot(generations, accuracy_3, label='Mutation Rate 0.1')
    plt.xlabel('Generations')
    plt.ylabel('Accuracy')
    plt.title('Convergence Over Generations')
    plt.legend()
    plt.show()

    data = {
        'Population Size': [50, 100, 150, 200],
        'Mutation Probability': [0.01, 0.05, 0.1, 0.2],
        'Accuracy': [0.75, 0.78, 0.80, 0.83]
    }

    df = pd.DataFrame(data)
    df_pivot = df.pivot(index="Population Size", columns="Mutation Probability", values="Accuracy")

    sns.heatmap(df_pivot, annot=True, cmap="YlGnBu")
    plt.title('Heatmap of Accuracy for Different Parameters')
    plt.show()

    data = {
    'Population Size': [50, 50, 50, 100, 100, 100, 150, 150, 150],
    'Accuracy': [0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83]
    }

    df = pd.DataFrame(data)
    sns.boxplot(x='Population Size', y='Accuracy', data=df)
    plt.title('Box Plot of Accuracy for Different Population Sizes')
    plt.show()

    data = {
    'Accuracy': [0.75, 0.78, 0.80, 0.83],
    'Time': [50, 70, 60, 90],
    'Mutation Rate': [0.01, 0.05, 0.1, 0.2]
    }

    df = pd.DataFrame(data)
    sns.scatterplot(x='Time', y='Accuracy', hue='Mutation Rate', data=df)
    plt.title('Scatter Plot of Accuracy vs Time for Different Mutation Rates')
    plt.show()



