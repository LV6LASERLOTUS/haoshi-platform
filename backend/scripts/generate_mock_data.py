"""Rebuild fictional organization/contact/note data based on the supplied screenshot.

Run from backend: python scripts/generate_mock_data.py
No external packages, real organizations, contacts, or personal data are used.
"""

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import random


AS_OF = date(2026, 11, 12)
PROFILES = [
    ("童學", ["兒童教育", "數位學習"], ["兒童", "青少年"]),
    ("青伴", ["青少年培力", "生涯探索"], ["青少年"]),
    ("銀齡", ["長者陪伴", "社區照顧"], ["長者"]),
    ("共融", ["身心障礙支持", "就業支持"], ["身心障礙者"]),
    ("家力", ["家庭支持", "婦女培力"], ["婦女", "家庭照顧者"]),
    ("山海", ["環境教育", "生態保育"], ["一般民眾", "兒童"]),
    ("毛伴", ["動物保護", "生命教育"], ["一般民眾"]),
    ("安心", ["疾病支持", "照顧者支持"], ["疾病患者", "家庭照顧者"]),
    ("鄰里", ["社區發展", "食物支持"], ["一般民眾", "弱勢家庭"]),
    ("新芽", ["多元文化", "生活適應"], ["新住民", "兒童"]),
    ("原力", ["文化保存", "地方發展"], ["原住民族", "青少年"]),
    ("藝起", ["藝術教育", "文化參與"], ["兒童", "一般民眾"]),
]
REGIONS = [("北區", ["臺北市", "新北市"]), ("中區", ["臺中市", "彰化縣"]),
           ("南區", ["臺南市", "高雄市"]), ("東區", ["花蓮縣", "臺東縣"])]
CONTACT_TYPES = {
    "培力課程": "需求盤點與專案規劃課程",
    "課後追蹤": "課程行動方案追蹤",
    "陪跑": "組織營運陪跑討論",
    "走訪": "服務現場走訪",
    "會員大會": "年度會員交流",
    "危機諮詢": "人力交接與專案風險諮詢",
    "獎補助入選": "示範獎補助入選通知與需求確認",
}
CONTACT_SOURCES = {
    "培力課程": "mock:course_attendance",
    "課後追蹤": "mock:pm_follow_up",
    "陪跑": "mock:coaching_log",
    "走訪": "mock:visit_log",
    "會員大會": "mock:member_meeting",
    "危機諮詢": "mock:consultation_log",
    "獎補助入選": "mock:award_log",
}
CONTACT_TEXT = [
    "對方希望先釐清分工與預期成果，合作意願仍待正式提案確認。",
    "參與者表示全職同仁有限，想了解可以分階段執行的做法。",
    "本次討論以內部流程為主，未談到承接企業計畫的能力。",
    "對方願意提供服務案例；尚未收到資料，不能視為已有佐證。",
    "有提出跨單位合作的想法，但決策者未出席，需要後續確認。",
    "此次活動參與積極；這是單次接觸觀察，不代表執行承諾。",
    "對方表示近期有交接安排，後續應確認承辦窗口。",
    "詢問財務整理工具；未取得財報，不能判斷財務狀況。",
]
NOTE_TEXT = [
    "上次討論能清楚說明服務對象，但跨部門分工還需要再對齊。這是當時觀察，宜與現況核對。",
    "對方提到想嘗試新做法，目前只有初步構想，尚無執行案例可供判斷。",
    "組織窗口回覆具體，決策仍須回到內部會議；不要將窗口意願等同全組織承諾。",
    "團隊熟悉在地需求，資料整理較分散。建議先協助盤點，不宜僅以資料量評價組織。",
    "先前交流節奏順暢，但近期人員可能異動，需再次確認目前窗口與可投入時間。",
    "本次僅短暫接觸，對執行能力沒有足夠依據，暫不下判斷。",
    "對方關心成效怎麼記錄，可能適合先做成果整理討論；實際參與意願待確認。",
]


def build_mock_dataset() -> dict:
    rng = random.Random(20261112)
    organizations = []
    for region_index, (label, regions) in enumerate(REGIONS):
        for profile_index, (name, issues, targets) in enumerate(PROFILES):
            index = len(organizations)
            organizations.append({
                "organization_id": f"ORG-{index + 1:03d}",
                "name": f"示範{name}{label}協會（虛構）",
                "issue_tags": None if index in (9, 31) else list(issues),
                "target_groups": None if index in (15, 37) else list(targets),
                "regions": None if index == 22 else [regions[profile_index % 2]],
                "membership_status": ["有效會員", "待續會", "非會員", None][(profile_index + region_index) % 4],
                "full_time_staff_count": [0, 1, 2, 3, 5, 8, 12, 20, None][(index * 5) % 9],
                "financial_report_type": ["收支報表", "財務報表", "查核簽證財報", None][(index * 3) % 4],
                "platform_listing_status": None,
                "support_tier": ["密集陪跑", "定期追蹤", "一般關懷", None][(profile_index * 3 + region_index) % 4],
                "source": "mock:organization_master",
            })

    # Six organizations have no contacts. A few have more contacts, without implying quality.
    contacted_ids = [o["organization_id"] for o in organizations[:42]]
    contact_orgs = contacted_ids + rng.choices(contacted_ids, weights=[5] * 4 + [1] * 38, k=158)
    contacts = []
    for index, org_id in enumerate(contact_orgs):
        contact_type = list(CONTACT_TYPES)[index % len(CONTACT_TYPES)]
        contacts.append({
            "contact_id": f"CONTACT-{index + 1:03d}",
            "organization_id": org_id,
            "date": (AS_OF - timedelta(days=rng.randint(0, 700))).isoformat(),
            "contact_type": contact_type,
            "activity_name": None if index % 19 == 0 else CONTACT_TYPES[contact_type],
            "participant_roles": None if index % 17 == 0 else [rng.choice(["執行長", "專案人員", "社工", "行政人員", "理事"])],
            "free_text": None if index % 7 == 0 else CONTACT_TEXT[index % len(CONTACT_TEXT)],
            "source": CONTACT_SOURCES[contact_type],
        })
    contacts.sort(key=lambda record: (record["date"], record["contact_id"]))

    # Fourteen distinct organizations have notes; some have multiple observations.
    noted_ids = [organizations[index]["organization_id"] for index in
                 (0, 2, 4, 7, 10, 12, 15, 19, 24, 29, 33, 38, 42, 46)]
    notes = []
    for index, org_id in enumerate(noted_ids + noted_ids[:6]):
        notes.append({
            "note_id": f"NOTE-{index + 1:03d}",
            "organization_id": org_id,
            "recorded_on": None if index % 9 == 0 else (AS_OF - timedelta(days=rng.randint(14, 900))).isoformat(),
            "author_role": "資深顧問" if index % 2 == 0 else "PM",
            "note_text": NOTE_TEXT[index % len(NOTE_TEXT)],
            "source": ["mock:consultant_notes", "mock:pm_notes", "mock:line_summary"][index % 3],
        })

    return {
        "schema_version": "0.2",
        "dataset_info": {
            "is_mock": True,
            "as_of_date": AS_OF.isoformat(),
            "description": "依組織主檔／接觸紀錄／顧問筆記欄位製作，全部為虛構資料。類別值為示範，非正式字典；上架欄原名待確認。",
        },
        "organizations": organizations,
        "contacts": contacts,
        "consultant_notes": notes,
        "task_cards": [
            {
                "task_id": "TASK-001",
                "title": "為一個計畫找對的組織",
                "scenario": "企業想用專業陪跑 10 家組織，PM 要把需求轉成條件，提出候選名單與理由。",
                "user_role": "PM",
                "questions": ["哪些需求能對應到現有主檔欄位？", "有哪些接觸紀錄或顧問觀察可佐證？", "哪些條件沒有資料，必須另外確認？"],
                "requested_organization_count": 10,
            },
            {
                "task_id": "TASK-002",
                "title": "讓散落的資料變成好用的入口",
                "scenario": "讓剛到職的 PM 接到電話時，30 秒就看懂這家組織。",
                "user_role": "新到職 PM",
                "questions": ["這家組織關注什麼、服務誰、在哪裡？", "最近有哪些接觸與留下的話？", "顧問如何描述，觀察來自何時何處？"],
                "requested_organization_count": None,
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "docs" / "recommendation-example.json")
    args = parser.parse_args()
    payload = build_mock_dataset()
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(payload['organizations'])} organizations, {len(payload['contacts'])} contacts, "
          f"{len(payload['consultant_notes'])} notes for 14 organizations, 2 task cards")


if __name__ == "__main__":
    main()
