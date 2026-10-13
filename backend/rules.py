"""Decisões rastreáveis com limiares didáticos, não prescrição agronômica."""
from .catalog import RULE_VERSION

LEVELS = {"baixo": 0, "atencao": 1, "alto": 2, "indisponivel": 3}


def decide(row, probability, available=True):
    if not available:
        return {"level": "indisponivel", "label": "Dados desatualizados", "action": "Verificar sensor e restabelecer a coleta antes de decidir.", "rules": [{"id": "Q01", "level": "indisponivel", "reason": "Não há 24 leituras válidas no último dia da janela."}], "version": RULE_VERSION}
    triggered = []
    def rule(condition, rule_id, level, reason):
        if condition:
            triggered.append({"id": rule_id, "level": level, "reason": reason})
    soil, temp = row["soil_moisture_pct"], row["temp_max"]
    rule(soil < 25, "R01", "alto", f"Umidade média do solo em {soil:.1f}%, abaixo de 25%.")
    rule(25 <= soil < 40, "R02", "atencao", f"Umidade média do solo em {soil:.1f}%, abaixo de 40%.")
    rule(temp >= 35 and soil < 35, "R03", "alto", f"Temperatura máxima de {temp:.1f} °C e umidade do solo abaixo de 35%.")
    rule(row["chuva_acum_7d"] < 10 and row["ndvi_tendencia_7d"] < -0.04, "R04", "atencao", "Chuva de 7 dias abaixo de 10 mm e queda de NDVI superior a 0,04.")
    rule(probability is not None and probability >= 0.7, "M01", "alto", f"Random Forest estima risco de seca ≥70% ({(probability or 0):.1%}).")
    rule(probability is not None and 0.5 <= probability < 0.7, "M02", "atencao", f"Random Forest estima risco de seca entre 50% e 70% ({(probability or 0):.1%}).")
    level = max((r["level"] for r in triggered), key=LEVELS.get, default="baixo")
    labels = {"baixo": "Estável", "atencao": "Atenção", "alto": "Alto risco"}
    actions = {"baixo": "Manter o acompanhamento e conferir a próxima leitura.", "atencao": "Conferir o talhão e a umidade do solo nas próximas 24 horas.", "alto": "Priorizar inspeção do talhão e avaliar a necessidade de irrigação com o responsável técnico."}
    return {"level": level, "label": labels[level], "action": actions[level], "rules": triggered or [{"id": "R00", "level": "baixo", "reason": "Nenhum limiar de alerta foi atingido."}], "version": RULE_VERSION}
