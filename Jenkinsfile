pipeline {
    // 在任何可用的 Jenkins Agent 上运行
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                // Jenkins 从 SCM 检出代码，此步骤由 Pipeline 定义自动完成
                echo '代码已拉取'
            }
        }

        stage('Setup Python Environment') {
            steps {
                // 在容器内安装 Python、Pip 和所需依赖
                sh '''
                    apt-get update -y
                    apt-get install -y python3 python3-pip
                    pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Pytest Tests') {
            steps {
                // 运行你的 Selenium 测试用例，并生成 JUnit 格式的报告
                // 这里假设你的测试文件在以 test_ 开头的文件中
                sh '''
                    python3 -m pytest -v --junitxml=reports/results.xml
                '''
            }
        }
    }

    post {
        always {
            // 无论构建成功还是失败，都会执行此步骤来收集测试报告
            junit 'reports/results.xml'
            // 如果你使用了 HTML 报告插件，可以在这里发布
            // publishHTML (target: [reportDir: 'reports', reportFiles: 'report.html', reportName: 'HTML Test Report'])
        }
    }
}