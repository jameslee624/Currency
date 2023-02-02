import csv

with open("currency_list.csv", "w") as fc:
    writer = csv.writer(fc)
    writer.writerow(["currency_code", "currency"])
    with open("currency_list.txt", "r") as ft:
        temp = []
        for idx, line in enumerate(ft):
            if idx < 12:
                continue
            elif idx % 2 == 0:
                temp.append(line[:-3])
            else:
                temp.append(line[:-1])
                writer.writerow(temp)
                temp = []