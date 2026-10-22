#!/usr/bin/env python3
"""
merge_and_clean.py — с дедупликацией по SEQN.
"""

import pandas as pd
from pathlib import Path
import gc

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

MISSING_THRESHOLD = 0.8


def main():
    print("=" * 70)
    print("Объединение NHANES: Пересечение с дедупликацией")
    print("=" * 70)

    PROC_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Загрузка demographics_clean.csv...")
    df_demo = pd.read_csv(RAW_DIR / "demographics_clean.csv", low_memory=False)
    print(f"    До дедупликации: {df_demo.shape[0]} строк × {df_demo.shape[1]} колонок")

    # Проверяем дубликаты SEQN в демографии
    demo_dups = df_demo.duplicated(subset=['SEQN']).sum()
    if demo_dups > 0:
        print(f"    ⚠ Найдено {demo_dups} дубликатов SEQN — удаляем")
        df_demo = df_demo.drop_duplicates(subset=['SEQN'], keep='first')
    print(f"    После дедупликации: {df_demo.shape[0]} строк")

    print("\n[2/3] Загрузка questionnaire_clean.csv...")
    df_quest = pd.read_csv(RAW_DIR / "questionnaire_clean.csv", low_memory=False)
    print(f"    До дедупликации: {df_quest.shape[0]} строк × {df_quest.shape[1]} колонок")

    # Проверяем дубликаты SEQN в опроснике
    quest_dups = df_quest.duplicated(subset=['SEQN']).sum()
    if quest_dups > 0:
        print(f"    ⚠ Найдено {quest_dups} дубликатов SEQN — удаляем")
        df_quest = df_quest.drop_duplicates(subset=['SEQN'], keep='first')
    print(f"    После дедупликации: {df_quest.shape[0]} строк")

    print("\n[3/3] Пересечение таблиц по 'SEQN'...")
    merged = pd.merge(df_demo, df_quest, on='SEQN', how='inner')

    # Запоминаем размер перед удалением
    min_rows = min(df_demo.shape[0], df_quest.shape[0])

    # Освобождаем память
    del df_demo, df_quest
    gc.collect()

    print(f"    ✓ Результат: {merged.shape[0]} строк × {merged.shape[1]} колонок")
    print(f"    (контроль: должно быть ≤ {min_rows} строк)")

    # Замена строковых 'NA' на настоящие пропуски
    print("\n Приведение пропусков к единому виду...")
    merged = merged.replace(['NA', 'na', 'N/A', ''], pd.NA)

    # Удаление колонок с >50% пропусков
    print(f"\n🗑 Удаление колонок с >{MISSING_THRESHOLD * 100:.0f}% пропусков...")
    missing_pct = merged.isnull().mean()
    cols_to_drop = missing_pct[missing_pct > MISSING_THRESHOLD].index.tolist()

    print(f"   Будет удалено колонок: {len(cols_to_drop)}")

    merged_clean = merged.drop(columns=cols_to_drop)

    # Сохранение
    output_path = PROC_DIR / "nhanes_final_merged.csv"
    print(f"\n💾 Сохранение в {output_path}...")
    merged_clean.to_csv(output_path, index=False)

    print("\n" + "=" * 70)
    print("✅ ГОТОВО!")
    print("=" * 70)
    print(f"Итоговый размер: {merged_clean.shape[0]} строк × {merged_clean.shape[1]} колонок")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())