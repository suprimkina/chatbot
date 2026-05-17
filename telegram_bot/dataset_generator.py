import csv
import random
from collections import Counter

REFERENCE_SOLUTIONS = [
    {
        "title": "FizzBuzz",
        "solution": """for i in range(1, 101):
    if i % 15 == 0:
        print('FizzBuzz')
    elif i % 3 == 0:
        print('Fizz')
    elif i % 5 == 0:
        print('Buzz')
    else:
        print(i)""",
        "language": "python"
    },
    {
        "title": "Two Sum",
        "solution": """def two_sum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []""",
        "language": "python"
    },
    {
        "title": "Palindrome Check",
        "solution": """def is_palindrome(s):
    s = s.lower()
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True""",
        "language": "python"
    },
    {
        "title": "Factorial",
        "solution": """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)""",
        "language": "python"
    },
    {
        "title": "Reverse String",
        "solution": """def reverse_string(s):
    return s[::-1]""",
        "language": "python"
    },
    {
        "title": "SQL Second Highest",
        "solution": """SELECT MAX(salary) as SecondHighestSalary
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees)""",
        "language": "sql"
    },
    {
        "title": "Debounce Function",
        "solution": """function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}""",
        "language": "javascript"
    }
]

def generate_correct(solution):
    return random.choice([
        solution,
        solution.replace("    ", "  "),
        solution + "\n",
    ])

def generate_syntax_error(solution):
    errors = [(":", ""), (")", ""), ("(", ""), (":", ";"), ("'FizzBuzz'", "FizzBuzz"),
              ("def ", "def$ "), ("def ", "Def "), ("if ", "If "), ("for ", "For "),
              ("return ", "Return "), (", ", " ")]
    sol = solution
    for old, new in random.sample(errors, k=random.randint(1, min(3, len(errors)))):
        if old in sol:
            sol = sol.replace(old, new, 1)
    return sol

def generate_logic_error(solution):
    logic_errors = [
        ("range(1, 101)", "range(1, 100)"), ("range(1, 101)", "range(0, 101)"),
        ("range(1, 101)", "range(101)"), ("i % 15 == 0", "i % 15 == 1"),
        ("i % 3 == 0", "i % 3 == 1"), ("i % 5 == 0", "i % 3 == 0"),
        ("<", "<="), (">", ">="), ("==", "="), ("!=", "=="),
        ("left < right", "left <= right"), ("n <= 1", "n < 1"),
        ("n <= 1", "n == 1"), ("return True", "return False"),
        ("return False", "return True"), ("return 1", "return 0"),
        ("n * factorial(n - 1)", "n + factorial(n - 1)"),
        ("left += 1", "left -= 1"), ("right -= 1", "right += 1"),
        ("left += 1\n        right -= 1", "left += 1")
    ]
    sol = solution
    for old, new in random.sample(logic_errors, k=random.randint(1, min(2, len(logic_errors)))):
        if old in sol:
            sol = sol.replace(old, new, 1)
    return sol

def generate_style_issue(solution):
    if "return s[::-1]" in solution:
        return solution.replace("return s[::-1]", """result = []
for i in range(len(s)-1, -1, -1):
    result.append(s[i])
return ''.join(result)""")
    # fallback
    return solution + "\n# TODO: optimize this code"

def generate_dataset(output_file="error_dataset.csv", samples_per_class=200):
    rows = []
    classes = ["correct", "syntax_error", "logic_error", "style_issue"]
    generators = {
        "correct": generate_correct,
        "syntax_error": generate_syntax_error,
        "logic_error": generate_logic_error,
        "style_issue": generate_style_issue
    }
    for ref in REFERENCE_SOLUTIONS:
        for cls in classes:
            gen = generators[cls]
            n = max(5, samples_per_class // len(REFERENCE_SOLUTIONS))
            for _ in range(n):
                try:
                    user_code = gen(ref["solution"])
                    if cls != "correct" and user_code == ref["solution"]:
                        continue
                    rows.append({
                        "user_code": user_code,
                        "reference_code": ref["solution"],
                        "label": cls,
                        "language": ref["language"],
                        "task_title": ref["title"]
                    })
                except Exception as e:
                    print(f"Ошибка генерации {ref['title']}/{cls}: {e}")

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_code", "reference_code", "label", "language", "task_title"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Датасет сохранён: {output_file}")
    print(f"Всего примеров: {len(rows)}")
    for label, cnt in Counter(r['label'] for r in rows).items():
        print(f"  {label}: {cnt}")

if __name__ == "__main__":
    generate_dataset()