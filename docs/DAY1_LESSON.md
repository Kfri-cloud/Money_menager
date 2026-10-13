# 1일차 학습 거래 한 건 입력하고 보여주기

이 과제의 첫날 목표는 용돈 기록 한 건을 키보드로 입력받고, 입력한 내용을 화면에 다시 보여주는 것이다. 오늘은 화면에서 값이 오가는 흐름을 익힌다. 과제의 파일 저장과 여러 명령은 다음 날부터 차례로 만든다.

**예상 시간:** 90분 정도. 20~25분마다 잠깐 쉬어도 좋다.

## 시작하기 전에

Python 3.10 이상이 필요하다. 터미널에서 `python --version`을 입력해 버전을 확인한다. `python` 명령이 동작하지 않는 환경에서는 설치된 Python 실행 명령을 사용한다.

실습 코드는 `Script/day1_practice.py`에 직접 입력한다. 파일을 저장한 뒤 저장소의 맨 위 폴더에서 다음처럼 실행한다.

```text
python Script/day1_practice.py
```

## 1단계 입력하고 출력하기 20분

아래 세 줄을 직접 입력하고 실행한다.

```python
category = input("무엇에 썼나요? ")
amount_text = input("얼마인가요? ")
print("분류:", category)
print("금액:", amount_text, "원")
```

`input()`은 입력한 글자를 받고, `print()`는 화면에 보여준다. `category`와 `amount_text`는 입력한 값을 잠시 담아 두는 이름이다.

**직접 바꿔 보기:** `category`에 `간식`, `amount_text`에 `3000`을 입력한다. 다음 실행에서는 `교통`, `1500`을 입력해 본다. 입력을 바꾸면 출력도 바뀌는지 확인한다.

## 2단계 글자를 숫자로 바꾸기 20분

`input()`이 받은 `3000`은 숫자처럼 보여도 글자다. 금액을 계산하려면 `int()`로 숫자로 바꾼다.

```python
amount_text = input("얼마인가요? ")
amount = int(amount_text)
print("지출 후 금액이 1000원 늘면", amount + 1000, "원")
```

**직접 확인하기:** `3000`을 입력하면 `4000`이 나온다. `삼천`을 입력하면 오류가 난다. 오류가 나더라도 코드를 지우지 말고, 어떤 입력에서 문제가 생겼는지 적어 둔다. 숫자가 아닌 입력을 친절하게 처리하는 방법은 뒤에서 배운다.

## 3단계 거래 한 건을 묶기 25분

한 번의 거래에는 날짜, 수입 또는 지출, 분류, 금액이 함께 있어야 한다. 파이썬의 **딕셔너리**는 이름표와 값을 한데 묶는다.

```python
transaction = {
    "date": "2026-09-30",
    "type": "expense",
    "category": "간식",
    "amount": 3000,
}

print(transaction["category"])
print(transaction["amount"])
```

`"category"`는 이름표이고 `"간식"`은 그 값이다. `transaction["category"]`는 그 이름표에 붙은 값을 꺼낸다.

**직접 바꿔 보기:** 날짜, 분류, 금액을 다른 예시로 바꾸고 다시 실행한다. `type`에는 수입이면 `income`, 지출이면 `expense`를 쓴다.

## 4단계 오늘의 작품 만들기 25분

`Script/day1_practice.py`의 연습 코드를 지우고, 아래 요구를 보고 **스스로** 다시 작성한다. 막히면 위의 예제를 하나씩 다시 실행해 본다.

1. `input()`으로 날짜, 종류, 분류, 금액을 차례로 받는다.
2. 금액을 `int()`로 숫자로 바꾼다.
3. 네 값을 `transaction` 딕셔너리에 넣는다.
4. `print()`로 입력한 거래를 한 줄씩 보여준다.

입력 예시는 `2026-09-30`, `expense`, `간식`, `3000`이다. 출력 문구는 달라도 되지만 입력한 네 값이 모두 보여야 한다.

<details>
<summary>막힐 때 펼쳐 보는 예시 코드</summary>

```python
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

print("날짜:", transaction["date"])
print("종류:", transaction["type"])
print("분류:", transaction["category"])
print("금액:", transaction["amount"], "원")
```

</details>

## 다 했는지 확인하기

- [ ] 내 컴퓨터에서 실습 파일을 직접 실행했다.
- [ ] 간식 지출과 용돈 수입을 각각 한 번 입력했다.
- [ ] `input()`, `int()`, `print()`가 하는 일을 내 말로 설명할 수 있다.
- [ ] 딕셔너리에서 `"amount"`가 이름표이고 금액 숫자가 값이라는 것을 설명할 수 있다.
- [ ] 프로그램을 다시 실행하면 입력했던 내용이 사라진다는 것을 확인했다. 파일 저장은 2일차에 배운다.

**시간이 남으면:** 거래에 `memo`(메모)와 `tags`(태그)도 추가해 본다. 둘은 과제에서 선택 입력이다. 오늘은 입력하고 보여주기까지만 하면 된다.

**함께 돕는 어른에게:** 답을 먼저 보여주기보다 아이에게 `입력한 값이 어디에 저장되어 있지?`, `왜 금액에 int()가 필요하지?`라고 물어본다. 오류가 나면 오류 메시지의 마지막 줄과 방금 입력한 값을 같이 읽는다.
