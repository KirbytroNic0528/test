from langchain_community.chat_models import ChatZhipuAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
import json
zhipuai_api_key = '4a478b99108ee30c1ae4aaa0aefe6632.X8sj7A6gaBgWh9AE'
llm = ChatZhipuAI(
    api_key=zhipuai_api_key,
    model="glm-4-plus",
    temperature=0.5,
)


prompt = ChatPromptTemplate.from_template(f"""你是一名代码专家请你认真读这个workflow，告诉我为什么我在github secret中创建了API_KEY这个仓库secret但无法被读取到")
{{workflow}}    
    """)
workflow ="""  
      name: coverage_and_test

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  build:
    strategy:
      matrix:
        os: [ ubuntu-latest ]
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      
      - name: install
        run: |
          curl -fsSL https://cli.moonbitlang.com/install/unix.sh | bash
          echo "$HOME/.moon/bin" >> $GITHUB_PATH
      - name: moon version
        run: |
          moon version --all
          moonrun --version

      - name: moon check
        run: moon check --deny-warn

      - name: moon info
        run: |
          moon info
          git diff --exit-code

      - name: Set ulimit and run moon test
        run: |
          ulimit -s 8176
          moon test --target all
          moon test --release --target all

      - name: moon bundle
        run: moon bundle --all

      - name: check core size
        run: find ./target -name '*.core' | xargs ls -lh

      - name: format diff
        run: |
          moon fmt
          git diff --exit-code

  test:
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
        with:
          python-version: '3.9'
        env:
          API_KEY: ${{ secrets.API_KEY }}
                   
      - name: install
        run: |
          curl -fsSL https://cli.moonbitlang.com/install/unix.sh | bash
          echo "$HOME/.moon/bin" >> $GITHUB_PATH
          
      - name: initial moon test
        run: moon test --enable-coverage
             
             moon coverage report -f coveralls

      - name: initial coverage report
        run: |
          moon coverage report -f summary > coverage_summary.txt
          cat coverage_summary.txt >> "$GITHUB_STEP_SUMMARY"
      
      - name: Install dependencies
        run: |
          pip install -r scripts/requirements.txt
          
      - name: loop coverage improvement
        env:
          API_KEY: ${{ secrets.API_KEY }}
        id: loop-coverage
        run:
         prev_coverage=$(cat coverage_summary.txt | grep 'Total Coverage' | awk '{print $NF}' | tr -d '%')  
         max_iterations=5  
         iteration=0  
         coverage_improved=true  
  
         while [ "$coverage_improved" = true ] && [ $iteration -lt $max_iterations ]; do
         
           python scripts/testagent.py --api_key ${{ secrets.API_KEY }}
           
           moon test --enable-coverage
           
           moon coverage report -f coveralls
           
           moon coverage report -f summary summary > coverage_summary.txt
           
           new_coverage=$(cat coverage_summary.txt | grep 'Total Coverage' | awk '{print $NF}' | tr -d '%')
           
           if [ $(echo "$new_coverage > $prev_coverage" | bc) -eq 1 ]; then
           
             prev_coverage=$new_coverage
             
             echo "Coverage improved to $new_coverage%"
             
           else
             coverage_improved=false
             
             echo "Coverage did not improve. Stopping loop."
             
           fi
           
           iteration=$((iteration + 1))
           
         done

      - name: coverage report
        run: |
          cat coverage_summary.txt >> "$GITHUB_STEP_SUMMARY"
          moon coverage report -f coveralls -o codecov_report.json --service-name github --service-job-id "$GITHUB_RUN_NUMBER" --service-pull-request "${{ github.event.number }}" --send-to coveralls
        env:
          COVERALLS_REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  typo-check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      FORCE_COLOR: 1
      TYPOS_VERSION: v1.19.0
    steps:
      - name: download typos
        run: curl -LsSf https://github.com/crate-ci/typos/releases/download/$TYPOS_VERSION/typos-$TYPOS_VERSION-x86_64-unknown-linux-musl.tar.gz | tar zxf - -C ${CARGO_HOME:-~/.cargo}/bin

      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      - name: check typos
        run: typos

  license-header-check:
    runs-on: ubuntu-latest
    env:
      HAWKEYE_VERSION: v5.5.1
    steps:
      - uses: actions/checkout@v4
      - name: Download HawkEye
        run: curl --proto '=https' --tlsv1.2 -LsSf https://github.com/korandoru/hawkeye/releases/download/$HAWKEYE_VERSION/hawkeye-installer.sh | sh
      - name: Check License Header
        run: hawkeye check
          """

retriever_chain = (
    prompt
    | llm
    | StrOutputParser()
)


re = retriever_chain.invoke(workflow)
print(re)