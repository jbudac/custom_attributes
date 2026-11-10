# Custom Parameters (Vlastné parametre) pre Home Assistant

Integrácia, ktorá umožní zadefinovať **vlastné parametre** (napr. *Príkon [W]*, *Dátum výmeny batérie*, *Strana domu*) a pridať ich ku všetkým zariadeniam alebo entitám zvoleného typu (svetlo, vypínač, žalúzie…). Hodnotu parametra potom nastavíš priamo na stránke daného zariadenia.

## Ako to funguje

1. Na stránke integrácie klikneš na **Pridať parameter** a vyplníš:
   - **Názov** – napr. `Príkon`
   - **Systémový názov (service name)** – napr. `prikon`; ak ho necháš prázdny, vytvorí sa z názvu
   - **Typ hodnoty** – číslo, text, dátum, dátum a čas, áno/nie, výber zo zoznamu
   - **Jednotka** – napr. `W`, `h`, `km`
   - **Pridať k** – *Zariadenie* (jedna hodnota na zariadenie), *Entita* (jedna hodnota na každú entitu) alebo **oboje naraz**
   - **Typy zariadení / entít** – napr. `light`, `switch`, `cover`; dá sa dopísať aj ľubovoľná iná doména
   - **Ikona** (nepovinné)
2. Pri čísle nastavíš ešte minimum, maximum, krok a spôsob zadávania. Pri výbere zadáš možnosti a pri texte maximálnu dĺžku.
3. Každé zodpovedajúce zariadenie dostane novú entitu v sekcii **Konfigurácia**, napr. `number.kuchynske_svetlo_prikon`. Tam hodnotu zadáš.

| Typ | Entita | Jednotka |
|---|---|---|
| Číslo | `number` | skutočná merná jednotka (grafy, štatistiky) |
| Text | `text` | atribút `unit` |
| Dátum | `date` | – |
| Dátum a čas | `datetime` | – |
| Áno / Nie | `switch` | – |
| Výber zo zoznamu | `select` | atribút `unit` |

Každá entita parametra má atribúty `parameter`, `target_device_id` a pri hodnote pre entitu aj `target_entity_id`.

Ak zaškrtneš zariadenie aj entitu, hlavná entita zariadenia dostane do názvu ID entity, aby sa nemiešala s hodnotou zariadenia. Napr. `Kuchynské svetlo Príkon` (zariadenie) a `Kuchynské svetlo Príkon (light.kuchynske_svetlo)` (entita).

### Automaticky
- Novo pridané zariadenia a entity dostanú parameter automaticky (do ~5 sekúnd).
- Odstránené zariadenia prídu o svoju entitu parametra.
- Úprava parametra (ikonka ⋮ → *Prekonfigurovať*) zmení všetky jeho entity. Zadané hodnoty zostanú zachované.
- Zmazaním parametra sa odstránia všetky jeho entity aj hodnoty.

Hodnoty sú uložené v `.storage/custom_params.values` a prežijú reštart.

## Použitie v automatizáciách a šablónach

```yaml
# nastavenie hodnoty
action: number.set_value
target:
  entity_id: number.kuchynske_svetlo_prikon
data:
  value: 60

# súčet príkonu všetkých zapnutých svetiel
{{ states.light | selectattr('state','eq','on')
   | map(attribute='entity_id') | map('device_id')
   | map('device_entities') | sum(start=[])
   | select('match','number\..*_prikon$')
   | map('states') | map('float', 0) | sum }}
```

## Inštalácia cez HACS

1. Nahraj tento repozitár na svoj GitHub.
2. HACS → ⋮ → **Vlastné repozitáre** → URL repozitára, kategória **Integration**.
3. Nainštaluj **Custom Parameters** a reštartuj Home Assistant.
4. **Nastavenia → Zariadenia a služby → Pridať integráciu → Custom Parameters**.

Ručná inštalácia: skopíruj `custom_components/custom_params` do `config/custom_components/` a reštartuj HA.

Vyžaduje Home Assistant 2025.8 alebo novší. Otestované na verzii 2026.10.

## Obmedzenia
- Integrácia pracuje len s entitami v registri entít, teda s entitami, ktoré majú `unique_id`. Staré YAML entity bez neho sa neponúknu.
- Zakázané zariadenia a entity sa preskakujú.
- Hodnotu nie je možné zobraziť priamo medzi atribútmi pôvodnej entity, pretože tú vlastní iná integrácia. Parameter je preto samostatná entita priradená k tomu istému zariadeniu.

## Vývoj / testy

```bash
pip install -r requirements_test.txt
pytest
```
