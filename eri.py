from django.utils.crypto import get_random_string
from itertools import zip_longest

l1=[{'size': 15, 'quantity': 0, 'ppu': 5000, 'spu': 12000}, {'size': 12, 'quantity': 3, 'ppu': 5000, 'spu': 15000}, 
 {'size': 1, 'quantity': 40, 'ppu': 5000, 'spu': 15000},]
l2=[{'size': 12, 'quantity': 2},{'size': 1, 'quantity': 2}]




is_size_available=False

new_sizes=[]
for item in l1:
    if item["quantity"]!=0:
        new_sizes.append(item)
print(new_sizes)

print(len(l2))
# for item2 in l2:
#     item1_sizes=[]
#     for item1 in l1:
#         if item1["quantity"]!=0:
#             item1_sizes.append(item1["size"])
#     if item2["size"] not in item1_sizes:
#         print("not avaliable")
    
   
# print(item1_sizes)
   
# final_ppu_list=[]
# final_spu_list=[]
# for item2 in l1:
#     final_ppu_list.append(item2["ppu"])
#     final_spu_list.append(item2["spu"])
    
# if all(x==final_ppu_list[0] for x in final_ppu_list):
#     print("ppu same")
# else:
#     print("ppu not same")

# if all (x==final_spu_list[0] for x in final_spu_list):
#     print("spu same")

# else:
#     print("spu not same")

# checking_number=True
# while checking_number:
#     identifier = get_random_string(length=3, allowed_chars='0123456789')
#     print(identifier)
#     if int(identifier)==69:
#         print("FOund number")
#         checking_number=False
# dict1 = [{"size": "m", "quantity": 2,"ppu":30,"spu":10}, {"size": "drink", "quantity": 2,"ppu":50,"spu":30}]
# dict2 = [{"size": "m", "quantity": 1},{"size": "drink", "quantity": 5}]

# for item1,item2 in zip_longest(dict1,dict2,fillvalue={"size":"Eri"}):
#     print(item1["size"],item2.get("size"))
#     if item1["size"]==item2.get("size"):
#         item1["quantity"]-=item2.get("quantity")
#         if item1["quantity"] <0:
#             item1["quantity"]+=item2.get("quantity")

#             break;
#         item2["ppu"]=item1["ppu"]
#         item2["spu"]=item1["spu"]

# print(dict1)
# print(dict2)

# total=0
# for item in dict1:
#     total+=item["quantity"]*item["spu"]
# merged_dict = {}
# for item in dict1:
#     size = item["size"]
#     quantity = item["quantity"]
#     ppu = item["ppu"]
#     spu = item["spu"]

#     if size in merged_dict:
#         merged_dict[size]["quantity"] += quantity
#         merged_dict[size]["ppu"] = ppu
#         merged_dict[size]["spu"] = spu

#     else:
#         merged_dict[size] = {"size":size,"quantity":quantity,"ppu":ppu,"spu":spu}

# for item in dict2:
#     size = item["size"]
#     quantity = item["quantity"]
#     ppu = item.get("ppu",0)
#     spu = item.get("spu",0)
    
#     if size in merged_dict:
#         merged_dict[size]["quantity"] += quantity
#         #merged_dict[size]["ppu"] = ppu
#     else:
#         merged_dict[size] = {"size":size,"quantity":quantity,"ppu":ppu,"spu":spu}


# #result=[{"size":size,"quantity":quantity} for size,quantity in merged_dict.items()]
# print(list(merged_dict.values()))

