from pathlib import Path
import json



def main():
    write_=write()
    save_=save(write_)
    load_=load(save_)

def write():
    date = input("날짜(YYYY-MM-DD): ")
    kind = input("종류(income/expense): ")
    category = input("분류: ")
    amount = int(input("금액: "))
    transaction = {
        "date": date,
        "type": kind,
        "category": category,
        "amount": amount,
        }
    
    return transaction

def save(transaction):

    data_dir=Path("data")
    data_dir.mkdir(exist_ok=True)
    for filename in ("transaction.jsonl","category.jsonl","budgets.jsonl"):
        (data_dir/filename).touch(exist_ok=True)
    transaction_file =data_dir/"transaction.jsonl"
    with transaction_file.open("a",encoding="utf-8")as file:
        file.write(json.dumps(transaction,ensure_ascii=False)+"\n")
    return transaction_file

def load(transaction_file):
    with transaction_file.open("r",encoding="utf-8") as file:
        for line in file:
            save_transaction= json.loads(line)
            print(save_transaction["date"],save_transaction["type"],
                save_transaction["category"],save_transaction["amount"],"원")


if __name__=="__main__":
    main()
    