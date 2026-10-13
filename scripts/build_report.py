"""Gera o relatório acadêmico consolidado (requer reportlab e Pillow)."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.pipeline import run_pipeline
from backend.simulator import simulate

OUT = ROOT / "output" / "pdf" / "agroorbit-fase6-relatorio.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
W, H = A4
M, CONTENT = 44, W - 88
GREEN, INK, MUTED, LIGHT, LINE = [colors.HexColor(c) for c in ("#274b35", "#283b2d", "#718069", "#f2f5eb", "#dfe7d6")]
pdf = canvas.Canvas(str(OUT), pagesize=A4)
pdf.setTitle("AgroOrbit Horizon - Fase 6 - Plataforma integrada")
pdf.setAuthor("Equipe AgroOrbit - material preparado com assistência de IA")
style = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, spaceAfter=8)
small = ParagraphStyle("small", parent=style, fontSize=8, leading=11, textColor=MUTED)
table_style = ParagraphStyle("cell", parent=style, fontSize=8.3, leading=11.5)
heading_style = ParagraphStyle("headcell", parent=table_style, fontName="Helvetica-Bold", textColor=GREEN)
page_num = 0


def text(content, x=M, y=150, width=CONTENT, kind=style):
    normalized = content.replace("—", "-").replace("–", "-").replace("→", " / ").replace("≥", ">=").replace("≤", "<=")
    p = Paragraph(normalized, kind)
    _, height = p.wrap(width, H)
    if y + height > H - 58:
        raise ValueError(f"Texto ultrapassa página {page_num}: {content[:60]} ({y + height})")
    p.drawOn(pdf, x, H - y - height)
    return y + height + 11


def line(content, x, y, size=10, color=INK, bold=False):
    pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    pdf.setFillColor(color)
    pdf.drawString(x, H - y, content)


def table(headers, rows, y, widths):
    data = [[Paragraph(escape(str(c)), heading_style) for c in headers]] + [[Paragraph(escape(str(c)), table_style) for c in row] for row in rows]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbf7")]), ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("LINEBELOW", (0, 0), (-1, 0), 0.7, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))
    _, height = t.wrap(CONTENT, H)
    if y + height > H - 62:
        raise ValueError(f"Tabela ultrapassa página {page_num}: {y + height}")
    t.drawOn(pdf, M, H - y - height)
    return y + height + 17


def start(section, title, subtitle=None):
    global page_num
    if page_num:
        pdf.showPage()
    page_num += 1
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, W, H, fill=1, stroke=0)
    line("AGROORBIT  /  HORIZON", M, 40, 8, GREEN, True)
    pdf.setStrokeColor(LINE)
    pdf.line(M, H - 55, W - M, H - 55)
    line(section.upper(), M, 86, 8, MUTED)
    line(title, M, 119, 24, GREEN, True)
    if subtitle:
        text(subtitle, y=134, kind=small)
    pdf.line(M, 45, W - M, 45)
    line("PBL AgroSmart | Fase 6 | Dados sintéticos e execução local", M, H - 30, 7.5, MUTED)
    line(f"{page_num:02d}", W - M - 12, H - 30, 8, GREEN, True)


def picture(filename, y, max_height=520, caption=None):
    image = ImageReader(str(ROOT / "docs" / "evidencias" / filename))
    iw, ih = image.getSize()
    scale = min(CONTENT / iw, max_height / ih)
    width, height = iw * scale, ih * scale
    x = M + (CONTENT - width) / 2
    pdf.drawImage(image, x, H - y - height, width=width, height=height, mask="auto")
    pdf.setStrokeColor(LINE)
    pdf.rect(x, H - y - height, width, height, fill=0, stroke=1)
    return text(caption, y=y + height + 12, kind=small) if caption else y + height


snapshot = json.loads((ROOT / "data" / "sample" / "dashboard.json").read_text())
meta = json.loads((ROOT / "entrega.json").read_text())
model = json.loads((ROOT / "models" / "export_validation.json").read_text())
browser = json.loads((ROOT / "docs" / "evidencias" / "browser-validation.json").read_text())
video_path = ROOT / "output" / "video" / "video-info.json"
video = json.loads(video_path.read_text()) if video_path.is_file() else None
scenarios = {name: run_pipeline(*simulate(name, "faz-002", 42))[0] for name in ("baseline", "seca", "chuva", "falha")}

# 1: capa
start("Atividade avaliativa", "Plataforma inteligente integrada")
pdf.setFillColor(GREEN)
pdf.roundRect(M, H - 393, CONTENT, 229, 14, fill=1, stroke=0)
line("AGROORBIT", M + 26, 213, 34, colors.HexColor("#e8f0d5"), True)
line("H O R I Z O N", M + 27, 238, 12, colors.HexColor("#bdcf94"))
line("Do campo ao próximo movimento.", M + 27, 295, 18, colors.white)
line("Sensores. Dados confiáveis. Decisões com evidências.", M + 27, 326, 10, colors.HexColor("#c9d8ba"))
line("FASE 6  /  PBL AGROSMART", M + 27, 364, 8, colors.HexColor("#b9ce9d"), True)
y = text("A solução integra coleta ambiental simulada, preparação em Python, um modelo de risco de seca reaproveitado do AgroOrbit AI, regras automatizadas e um dashboard analítico. Esta fase evolui a base da Fase 5 para um fluxo executável e reproduzível.", y=418)
y = table(["Escopo demonstrado", "Resultado verificável"], [["3 propriedades / 14 dias", "1.008 leituras horárias válidas no lote habitual"], ["Modelo + regras", "300 árvores e decisões vinculadas aos eventos de origem"], ["Entrega funcional", "Código, datasets, capturas, relatório e vídeo"]], y + 6, [210, CONTENT - 210])
y = text(f"<b>Integrante identificado:</b> Samuel Ramos de Almeida - RM99134.<br/><b>Turma:</b> {escape(meta.get('class_name') or 'a confirmar')}. Demais integrantes aguardam confirmação. O enunciado exige equipe de 3 a 5 alunos.", y=y + 6, kind=small)
text("Material acadêmico com assistência de IA. Os dados ambientais são sintéticos. A revisão e a submissão final cabem à equipe.", y=y + 3, kind=small)

# 2: arquitetura
start("01 / Arquitetura", "Um fluxo completo e rastreável", "O diagrama corresponde aos componentes executados nesta entrega.")
nodes = [(44, 189, "01 / SENSORES", "Coleta virtual", "Temperatura, solo, luz, chuva"), (224, 189, "02 / BRONZE", "Eventos originais", "JSONL, lote, event_id"), (404, 189, "03 / SILVER", "Dados validados", "Schema, faixa e deduplicação"), (404, 345, "04 / GOLD", "Features diárias", "Janelas de 7 e 14 dias"), (224, 345, "05 / AUTOMAÇÃO", "Modelo + regras", "Risco, motivos e ação"), (44, 345, "06 / DASHBOARD", "Análise visual", "Indicadores e alertas")]
for x, y, cap, title, detail in nodes:
    pdf.setFillColor(LIGHT)
    pdf.setStrokeColor(LINE)
    pdf.roundRect(x, H - y - 106, 147, 106, 9, fill=1, stroke=1)
    line(cap, x + 12, y + 25, 7, MUTED, True)
    line(title, x + 12, y + 51, 12, GREEN, True)
    text(detail, x=x + 12, y=y + 67, width=122, kind=small)
def arrow(x1, y1, x2, y2):
    pdf.setStrokeColor(colors.HexColor("#94a578"))
    pdf.setFillColor(colors.HexColor("#94a578"))
    pdf.setLineWidth(1.6)
    pdf.line(x1, H - y1, x2, H - y2)
    p = pdf.beginPath()
    if y1 == y2:
        s = 1 if x2 > x1 else -1
        p.moveTo(x2, H - y2); p.lineTo(x2 - s * 6, H - y2 + 3); p.lineTo(x2 - s * 6, H - y2 - 3)
    else:
        p.moveTo(x2, H - y2); p.lineTo(x2 - 3, H - y2 + 6); p.lineTo(x2 + 3, H - y2 + 6)
    p.close(); pdf.drawPath(p, fill=1, stroke=0)
arrow(191, 242, 219, 242); arrow(371, 242, 399, 242); arrow(477, 295, 477, 339); arrow(404, 398, 376, 398); arrow(224, 398, 196, 398)
pdf.setFillColor(colors.HexColor("#f1e8d9")); pdf.roundRect(M, H - 531, CONTENT, 51, 7, fill=1, stroke=0)
text("<b>Desvio de qualidade:</b> registros inválidos e conflitos vão para quarentena com payload e motivo. Retransmissões idênticas são removidas antes da Silver.", x=M + 13, y=491, width=CONTENT - 26, kind=small)
y = text("O dashboard React chama uma API Python local para executar o cenário. A API publica o snapshot e os arquivos do mesmo lote de forma consistente. Cada execução preserva Bronze, Silver, Gold, alertas, qualidade e checksums.", y=557)
y = text("A organização Bronze/Silver/Gold é implementada em arquivos locais. O modelo anterior foi exportado com seus pré-processadores. A CNN do AgroOrbit Vision é uma referência para continuidade, mas não participa da inferência desta fase.", y=y)
text("Implementações: backend/simulator.py, pipeline.py, model.py, rules.py e server.py. Diagrama vetorial completo: docs/arquitetura.svg.", y=y + 4, kind=small)

# 3: coleta
start("02 / Coleta do ambiente", "Sensores que podem ser reproduzidos", "Simulador em software como ferramenta equivalente admitida pelo enunciado.")
y = text("O simulador gera 14 dias de leituras horárias para três propriedades fictícias. A semente controla o ruído de forma determinística; cada fazenda possui sua própria sequência aleatória. Um cenário aplicado à Boa Vista não altera as outras propriedades.", y=172)
y = table(["Sensor", "Unidade", "Comportamento"], [["Temperatura ambiente", "°C", "Ciclo diário; elevação no cenário de seca"], ["Umidade do solo", "% relativo", "Escala simulada de 0 a 100; sem calibração física"], ["Luminosidade", "lux", "Curva diurna e valores próximos de zero à noite"], ["Pluviômetro", "mm / hora", "Incremento por intervalo; somado para chuva diária"]], y, [128, 80, CONTENT - 208])
y = text("<b>Contexto orbital:</b> NDVI, NDWI e cobertura de nuvens são gerados sinteticamente para manter as entradas do modelo anterior. Não são medições do circuito nem downloads de Sentinel-2 nesta execução.", y=y)
y = table(["Cenário", "Efeito no alvo"], [["Habitual", "Reconstrói o monitoramento-base"], ["Estresse hídrico", "Solo e chuva diminuem; temperatura sobe; NDVI cai"], ["Recuperação após chuva", "Umidade e vegetação se recuperam gradualmente"], ["Falha de sensor", "24 leituras do último dia ficam inválidas"]], y, [155, CONTENT - 155])
text("Janela: 01-14/09/2026, UTC. O experimento é processado em lote, não em streaming. Código: backend/simulator.py. Dados gerados: data/sample/bronze.jsonl. Captura: docs/evidencias/02-simulador.png.", y=y + 4, kind=small)

# 4: processamento
start("03 / Preparação dos dados", "Qualidade antes da análise", "Reconciliação real do lote habitual, semente 42.")
y = table(["Etapa", "Controle aplicado"], [["Contrato", "Campos obrigatórios, telemetry.v2, origem simulada e talhão cadastrado"], ["Horário", "Timezone obrigatório, hora inteira e janela válida"], ["Medidas", "Números finitos dentro das faixas do contrato"], ["Duplicatas", "source + event_id; conflito de conteúdo é rejeitado"], ["Gold", "Agregação por propriedade e dia; janelas de calendário"]], 177, [104, CONTENT - 104])
q = snapshot["quality"]
y = table(["Recebidos", "Aceitos", "Quarentena", "Duplicatas", "Aceitação"], [[q["received"], q["accepted"], q["quarantined"], q["duplicates"], f"{q['acceptance_pct']:.2f}%"]], y + 4, [CONTENT / 5] * 5)
y = text("As médias de solo, temperatura e luminosidade são diárias. Chuva é soma dos incrementos horários. A Gold também contém extremos térmicos, chuva acumulada, sequência de dias sem chuva e variação do NDVI contra sete dias antes.", y=y + 3)
y = text("O modelo só recebe inferência após 14 dias completos. Não se preenchem lacunas como se fossem observações. Se o último dia do talhão estiver incompleto, o painel marca a condição atual como indisponível.", y=y)
y = text("<b>Replay e idempotência:</b> o script pode reler o Bronze preservado. Os testes exigem que todos os arquivos de saída mantenham exatamente os mesmos hashes SHA-256 ao reprocessar o mesmo lote.", y=y)
text("Exemplos do dataset processado: data/sample/silver.csv e gold.csv. Motivos de rejeição: quarantine.json. Resumo de qualidade: quality.json. Código: backend/pipeline.py.", y=y + 4, kind=small)

# 5: automação
start("04 / Automação inteligente", "Uma recomendação com motivos", "Random Forest legado + motor de regras. A maior severidade define a prioridade.")
y = text("O modelo portátil reproduz OneHotEncoder, StandardScaler e 300 árvores do agroorbit-ai. Foram comparadas 500 entradas com a versão original; o erro absoluto máximo foi menor que 10<super>-12</super>. Isso verifica paridade de software, não acurácia em campo.", y=172)
y = table(["Regra", "Condição", "Resultado"], [["Q01", "Último dia ausente ou com menos de 24 leituras", "Indisponível"], ["R01", "Solo <25%", "Alto risco"], ["R02", "25% <= solo <40%", "Atenção"], ["R03", "Máxima >=35 °C e solo <35%", "Alto risco"], ["R04", "Chuva 7d <10 mm e variação NDVI <-0,04", "Atenção"], ["M01 / M02", "Probabilidade >=70% / de 50% a <70%", "Alto / atenção"], ["R00", "Nenhum limiar acionado", "Estável"]], y, [57, 338, CONTENT - 395])
rows = []
for name, label in [("baseline", "Habitual"), ("seca", "Seca"), ("chuva", "Após chuva"), ("falha", "Falha")]:
    farm = scenarios[name]["farms"][1]
    latest = farm["latest"] if farm["available"] else None
    rows.append([label, f"{latest['soil_moisture_pct']:.1f}%" if latest else "Indisponível", f"{latest['risk_probability'] * 100:.1f}%" if latest and latest['risk_probability'] is not None else "Suspenso", farm["decision"]["label"]])
y = table(["Boa Vista / semente 42", "Solo", "Modelo", "Decisão final"], rows, y + 3, [145, 92, 92, CONTENT - 329])
text("A saída mantém lote, propriedade, versão das regras e eventos de evidência. Os motivos são regras explícitas, não SHAP. As recomendações exigem validação humana e não acionam equipamentos reais.", y=y, kind=small)

# 6: dashboard
start("05 / Dashboard analítico", "O campo visto pelos dados", "Captura real da interface; arquivos PNG originais acompanham o pacote.")
y = text("Indicadores, série temporal de 7 ou 14 dias e comparação entre propriedades. A fonte é o mesmo snapshot produzido pelo pipeline. O mapa é ilustrativo e não representa um contorno geográfico real.", y=171)
picture("01-dashboard.png", y + 7, max_height=495, caption="Figura 1. Visão do campo no cenário habitual. A indicação de alto risco pode resultar de uma regra ambiental mesmo quando a probabilidade do modelo está na faixa de atenção.")

# 7: simulador
start("06 / Evidência de integração", "O cenário muda. A análise acompanha.", "Captura real após executar estresse hídrico na Fazenda Boa Vista.")
y = text("A interface controla cenário e semente. Ao executar a simulação, sensores, dataset, inferência e alertas são recalculados no backend. A tabela mostra as últimas leituras válidas, com horário e event_id.", y=171)
picture("02-simulador.png", y + 7, max_height=495, caption="Figura 2. Sensores virtuais e execução do cenário. Temperatura, solo, luz e chuva do diagrama são leituras do lote processado. NDVI é contexto orbital sintético separado.")

# 8: verificações
start("07 / Validação", "Evidências que podem ser conferidas", "Testes automatizados, comparação do modelo e inspeção visual.")
y = table(["Verificação", "Evidência"], [["16 testes de backend", "Qualidade, faixas, deduplicação, isolamento, janelas, regras, replay, modelo e HTTP"], [f"{browser['passed']} testes de navegador", "Filtros, cenários, alertas, downloads, mobile, modo offline e ausência de erros JavaScript"], ["500 casos do modelo", "Paridade das previsões com o artefato original; tolerância de 1e-12"], ["Build de produção", "Interface React empacotada pelo Vite"], ["Capturas desktop e mobile", "docs/evidencias/01-dashboard.png a 08-mobile.png"]], 177, [145, CONTENT - 145])
y = text("<b>Comportamentos críticos:</b> a chuva é somada, não promediada; mudar o cenário de uma fazenda não altera as outras; falhas atuais não são ocultadas por valores antigos; as regras conservam os motivos; os downloads pertencem ao lote atual; o modo sem API é somente leitura.", y=y + 5)
y = text("<b>Limites conhecidos:</b> dados e rótulos de treinamento sintéticos, limiares didáticos, ausência de calibração do solo, ausência de validação em campo e operação exclusivamente local. Não há integração real com satélite, TinkerCad, MQTT ou WhatsApp nesta fase.", y=y)
y = text("<b>Continuidade para a Fase 7:</b> adaptar sensores reais ao contrato, integrar fontes climáticas e orbitais, avaliar o modelo por tempo e produtor, incorporar o módulo Vision em execução, acrescentar persistência de produção e autenticação e validar decisões com especialistas.", y=y)
text("Fontes de evidência: tests/; docs/evidencias/browser-validation.json; models/export_validation.json. Instruções completas e proveniência em README.md e docs/08-proveniencia.md.", y=y + 4, kind=small)

# 9: entrega
start("08 / Reprodução e entrega", "Tudo no mesmo pacote", "Conferir a identificação da equipe antes da submissão acadêmica.")
y = text("<b>Execução a partir do ZIP:</b> abra a pasta agroorbit-fase6 e execute <font name='Courier'>python3 -m backend.server</font>. A interface compilada já acompanha o pacote. Depois abra http://127.0.0.1:8766. No repositório, execute npm ci, npm run build e npm start.", y=172)
duration_text = f"{int(video['duration_seconds'] // 60)} min {round(video['duration_seconds'] % 60):02d} s" if video else "em preparação"
y = table(["Artefato", "Localização"], [["Código e instruções", "README.md, backend/, src/ e tests/"], ["Dados de entrada e saída", "data/sample/"], ["Arquitetura e explicações", "docs/01-arquitetura.md a 08-proveniencia.md"], ["Capturas da aplicação", "docs/evidencias/"], ["Relatório consolidado", "output/pdf/agroorbit-fase6-relatorio.pdf"], [f"Vídeo ({duration_text})", "output/video/agroorbit-fase6-demo.mp4"], ["Identificação da equipe", "entrega.json"]], y + 5, [165, CONTENT - 165])
y = text("<b>Demonstração:</b> o vídeo mostra a aplicação em execução e contém narração sintetizada em português. A equipe deve revisar imagem e áudio antes da submissão. O MP4 acompanha o pacote e também está disponível no link abaixo.", y=y)
if meta.get("video_url"):
    y = text(f'<link href="{escape(meta["video_url"])}" color="#274b35"><u>Assistir ao vídeo demonstrativo no GitHub (MP4)</u></link>', y=y)
else:
    y = text("Link do vídeo pendente: preencher video_url em entrega.json antes de submeter.", y=y)
y = text("<b>Pendências administrativas:</b> confirmar turma e completar os nomes e RMs dos 3 a 5 integrantes. O responsável identificado é Samuel Ramos de Almeida, RM99134. O empacotador final bloqueia identificação incompleta; uma versão de preparação registra as pendências dentro do ZIP.", y=y)
y = text("<b>Nome exigido:</b> nomecompleto_rm_turma_fase6_atividade.zip. Revise o conteúdo antes do envio: a atividade é submetida exclusivamente pela plataforma acadêmica.", y=y)
text("Repositórios de origem: github.com/agroorbit-org/agroorbit-fase5; agroorbit-ai; agroorbit-vision. Commits e hashes foram registrados em docs/08-proveniencia.md e models/export_validation.json.", y=y + 3, kind=small)
pdf.save()
print(json.dumps({"path": str(OUT), "pages": page_num, "video_duration": duration_text}, ensure_ascii=False))
