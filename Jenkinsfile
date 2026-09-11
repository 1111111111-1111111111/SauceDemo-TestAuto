pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/1111111111-1111111111/SauceDemo-TestAuto'
            }
        }

        stage('Prepare Python Env') {
            steps {
                bat '''
                    chcp 65001
                    python -m venv .venv
                    .venv\\Scripts\\python.exe -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
                    .venv\\Scripts\\python.exe -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
                '''
            }
        }

        stage('Run Auto Tests') {
            steps {
                bat '''
                    chcp 65001
                    .venv\\Scripts\\python.exe -m pytest --alluredir=allure-results
                '''
            }
        }
    }

    post {
        always {
            // 生成 Allure 报告
            allure includeProperties: false,
                   jdk: '',
                   results: [[path: 'allure-results']]

            // 归档测试结果与报告
            archiveArtifacts artifacts: 'allure-results/**', allowEmptyArchive: true

            // 发布 JUnit 测试结果（如果 pytest 生成了 junit xml）
            junit allowEmptyResults: true,
                  testResults: '**/test-results/*.xml'
        }
    }
}
