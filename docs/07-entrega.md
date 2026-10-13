# 7. Preparação para envio

O enunciado solicita um único `.zip` ou `.rar`, com documentos, códigos, datasets, capturas e vídeo ou link. O padrão de nome é `nomecompleto_rm_turma_fase6_atividade.zip`.

## Identificação

Trabalho individual de **Samuel Ramos de Almeida - RM99134**, conforme a modalidade informada pelo autor. Não há outros integrantes a cadastrar. A turma ainda precisa ser preenchida para compor o nome final do arquivo.

Edite `entrega.json` com a turma. O link público do vídeo já está preenchido: [assistir à demonstração de 3min43s](https://raw.githubusercontent.com/agroorbit-org/agroorbit-fase6/main/output/video/agroorbit-fase6-demo.mp4). O arquivo MP4 também acompanha o pacote. Se a instituição restringir os serviços aceitos, o autor pode publicar o mesmo vídeo em Drive ou YouTube e atualizar o link.

## Gerar o pacote

```bash
# Versão de preparação: inclui arquivo PENDENCIAS.txt se faltarem dados.
python3 scripts/package_delivery.py --draft

# Versão final: verifica identificação do autor, turma e vídeo.
python3 scripts/package_delivery.py
```

O empacotador inclui código-fonte, modelo exportado, dados, evidências, PDF, MP4, metadados, testes e `dist/` executável. Exclui `.git`, credenciais, dependências instaladas, ambientes virtuais, caches e execuções temporárias. Reabre o ZIP e verifica CRC antes de concluir.

## Checklist de conteúdo

- [x] Arquitetura e descrição dos componentes.
- [x] Simulador executável e descrição dos sensores.
- [x] Código de processamento e datasets Bronze/Silver/Gold.
- [x] Automação e exemplo de saída.
- [x] Dashboard e indicadores descritos.
- [x] Roteiro de demonstração.
- [x] Vídeo de 3 a 5 minutos e link direto para acesso público.
- [x] Identificar o único autor do trabalho individual.
- [ ] Preencher a turma.
- [ ] Revisar o vídeo; a narração utiliza voz sintetizada.
- [ ] Conferir o nome do arquivo final e enviar pela plataforma da disciplina.

Apenas preparar o arquivo não constitui submissão. Nenhum upload na plataforma acadêmica foi realizado automaticamente.
