import os 
import json


results_dict = {}

for folder in os.listdir('results/'):
    
    if 'overall_results.json' in os.listdir(f'results/{folder}'):
        with open(f'results/{folder}/overall_results.json', 'r') as f:
            results = json.load(f)

#         # if results["SIGNAL_VARIABLES"]["exit"]["buy_sold_ratio"] == 0.3:
#         results_dict[folder] = results['total_gain_loss_percentage']
        print(folder, results['total_gain_loss_percentage'])    


# results_dict = {k: v for k, v in sorted(results_dict.items(), key=lambda item: item[1], reverse=True)}
# i, show_top = 0, 10

# for k, v in results_dict.items():
#     if i < show_top:
#         i += 1
#     else:
#         break

#     with open(f'results/{k}/overall_results.json', 'r') as f:
#         results = json.load(f)

    # print(f"Variable hash: {k}")

    # print(results['total_gain_loss_percentage'])
    # print(results['SIGNAL_VARIABLES'])



