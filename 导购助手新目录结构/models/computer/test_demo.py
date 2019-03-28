from NLU import NLU_interface as NLU
from dialogue import Computer_Dialogue
import cgi


#
# NLU test
# while True:
#     text = input("请输入一个句子")
#     # 我想买一台5000块左右的电脑result
#     # 我想买台电脑，内存8G以上，cpu i7, 1T硬盘
#     slot = NLU.get_slot_dl(text)
#     print(slot)

# NLU Manger Test
# dialogue_test = Computer_Dialogue()

Task = Computer_Dialogue()
request = input('Customer:')
reply = ''
step = 0
while (step <= 12 ):
    print('Agent:' + Task.get_response(request))
    request = input('Customer:')
