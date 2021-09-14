from app import Users, Answer, Question,session

questions = session.query(Question).all()
li = []
for question in questions:
    sev = {}
    if question.answers:
        for answer in question.answers:
            sev["question"] = question.qtn
            sev["name"] = answer.user.username
            sev["answer"] = answer.ans
            li.append(sev)
print(li)

li2 = []
for question in questions:
    sev2 = dict()
    if question.answers:
        for ans in question.answers:
            sev2[question.qtn] = ans.ans
            li2.append(sev2)
print(li2)
    



