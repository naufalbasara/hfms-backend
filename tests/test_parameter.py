import requests, pandas as pd, numpy as np, os, matplotlib.pyplot as plt
import re, time
import seaborn as sns

from pprint import pprint

def get_rootdir() -> str:
    cwd = os.path.abspath(os.getcwd())
    end = re.search(r'hfms-backend', cwd).end()
    rootdir = cwd[:end]

    return rootdir

def convergence_generation():
    """
    To compare performance of algorithm in different mutation rate
    """
    print("Testing convergence for comparing different mutation rate parameter")
    for mutation_rate in param_grid['mutation_rate']:
        res = requests.post(endpoint, json=data_json, headers={
            'Mutation-Rate': f'{mutation_rate}',
            'Population-Size': '25',
            'Generations': '30'
        }).json()
        history = res.get('resultHistory', None)
        plt.plot([*range(1, 31)], history, label=f'Mutation Rate {mutation_rate}')
    
    plt.xlabel('Generations')
    plt.ylabel('Risk')
    plt.title('Convergence Over Generations')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, f'tests/test_result/parameter_benchmarking/convergence_generation.png'))

    return

def box_plot_performance():
    """
    To compare performance of algorithm in different population size
    """
    print("Testing different populations size parameter")
    result_data = {
    'Population Size': [],
    'Risk Reduction': []
    }
    for pop_size in param_grid['population_size']:
        for i in range(3):
            res = requests.post(endpoint, json=data_json, headers={
                'Mutation-Rate': '0.1',
                'Population-Size': f'{pop_size}',
                'Generations': '30'
            })
            riskReduction = res.json().get('recommendationResult', None).get('riskReduction', None)
            result_data['Risk Reduction'].append(riskReduction)
            result_data['Population Size'].append(pop_size)

    sns.boxplot(x='Population Size', y='Risk Reduction', data=pd.DataFrame(result_data))
    plt.title('Box Plot of Risk Reduction for Different Population Sizes')
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, f'tests/test_result/parameter_benchmarking/box_plot_performance.png'))

    return

def scatter_tradeoff():
    """
    To compare performance of the algorithm in different generation size
    """
    print("Testing convergence for comparing different generation size parameter")
    data = {
    'Risk Reduction': [],
    'Time': [],
    'Generation Size': []
    }

    for generation_size in param_grid['generation']:
        res = requests.post(endpoint, json=data_json, headers={
            'Mutation-Rate': f'0.2',
            'Population-Size': '25',
            'Generations': f'{generation_size}'
        }).json()

        riskReduction = res.get('recommendationResult', None).get('riskReduction', None)
        timeTaken = res.get('recommendationResult', None).get('timeTaken', None)

        data['Risk Reduction'].append(riskReduction)
        data['Time'].append(timeTaken)
        data['Generation Size'].append(generation_size)


    sns.scatterplot(x='Time', y='Risk Reduction', hue='Generation Size', data=pd.DataFrame(data))
    plt.title('Scatter Plot of Risk Reduction vs Time for Different Generation Sizes')
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, f'tests/test_result/parameter_benchmarking/scatter.png'))

    return

def bar_avg_performance():
    average_accuracy = [0.76, 0.79, 0.82, 0.85]
    population_sizes = [50, 100, 150, 200]

    plt.bar(population_sizes, average_accuracy)
    plt.xlabel('Population Size')
    plt.ylabel('Average Accuracy')
    plt.title('Bar Chart of Average Accuracy for Different Population Sizes')
    plt.show()

    return

if __name__ == '__main__':
    start_all_process = time.time()
    version = 3
    base_path = get_rootdir()
    data_path = os.path.join(base_path, 'tests/test_data/')

    data = pd.read_csv(os.path.join(data_path, 'positive_case.csv'))

    try:
        data = data.set_index('SEQN', drop=True)
        data['Quest16_MCQ160B'] = data['Quest16_MCQ160B'].astype(int)
        sampling_data = data.sample(n=1, random_state=43)
    except Exception as error:
        raise f"Error in reading data: {error}"
    
    param_grid = {
        'mutation_rate': np.arange(0.1, 1, 0.1).astype(float),
        'population_size': np.arange(20, 101, 20).astype(int),
        'generation': np.arange(10, 51, 10).astype(int),
    }
    
    endpoint = f'http://127.0.0.1:5000/v{version}/recommendations/'
    lifestyle = sampling_data.iloc[0, :22].to_dict()
    characteristic = sampling_data.iloc[0, 22:].to_dict()    
    data_json = {**lifestyle, **characteristic}

    # Run test here by uncomment.
    # convergence_generation()
    # box_plot_performance()
    # scatter_tradeoff()





