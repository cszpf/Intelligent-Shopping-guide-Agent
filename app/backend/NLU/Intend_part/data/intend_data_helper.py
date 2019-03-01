import pandas as pd

def get_data():

    answer_no_repeat_num = 10
    answer_yes_repeat_num = 10
    ask_slot_repeat_num = 10
    data_list = []
    label_list = []

    answer_no = pd.read_csv('./answer_no.csv')
    answer_yes = pd.read_csv('./answer_yes.csv')
    answer_slot = pd.read_csv('./answer_slot.csv')
    ask_slot_list = pd.read_csv('./ask_slot_list.csv')

    data_list.extend(answer_slot['sentence'])
    label_list.extend(['answer_slot' for i in range(len(answer_slot['sentence']))])

    for i in range(answer_no_repeat_num):
        data_list.extend(answer_no['sentence'])
        label_list.extend(['answer_no' for i in range(len(answer_no['sentence']))])
    for i in range(answer_yes_repeat_num):
        data_list.extend(answer_yes['sentence'])
        label_list.extend(['answer_yes' for i in range(len(answer_yes['sentence']))])
    for i in range(ask_slot_repeat_num):
        data_list.extend(ask_slot_list['sentence'])
        label_list.extend(['ask_slot_list' for i in range(len(ask_slot_list['sentence']))])

    data = pd.DataFrame()
    data['sentence'] = data_list
    data['label'] = label_list
    data.to_csv('./intend_data_1.csv', index=False)

if __name__ == "__main__":
    get_data()