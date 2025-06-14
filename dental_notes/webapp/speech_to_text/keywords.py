class Keywords:
    def __init__(self):
        self.keywords = {
            "floss": "Flossing is the process of cleaning between teeth using a thin, strong thread called dental floss to remove food particles and plaque from areas a toothbrush cannot easily reach",
            "gums": "Gums, also known as gingiva (plural: gingivae), are the mucosal tissue that covers the mandible and maxilla inside the mouth, surrounding and supporting the teeth",
            "partial": "For more information, see the <a href='/media/pdf/PartialDenture.pdf' target='_blank'>Partial Denture Guide</a>."
        }

    def detect_keywords(self, paragraph):
        explanations = []
        for keyword, explanation in self.keywords.items():
            if keyword.lower() in paragraph.lower():
                explanations.append(f"{keyword}: {explanation}")
        return explanations


# def detect_keywords(paragraph, keywords):
#     found_keywords = []
#     for keyword in keywords:
#         if keyword.lower() in paragraph.lower():
#             found_keywords.append(keyword)
#     return found_keywords

# 使用示例
# paragraph = "Python是一种高级编程语言，常用于数据分析和机器学习。"
# keywords = ["Python", "数据分析", "Java", "机器学习"]

# found = detect_keywords(paragraph, keywords)
# if found:
#     print(f"找到以下关键词：{', '.join(found)}")
# else:
#     print("未找到任何关键词")
