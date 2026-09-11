pipeline {
    // 在 Jenkins 节点上运行
    agent any

    options {
        // 只保留最近 10 次构建记录，避免构建历史无限累积占满磁盘
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // 显示时间戳，方便排查
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                // 从 GitHub 拉取代码（对应 Jenkins 任务里配置的 Git 仓库和凭据）
                checkout scm
            }
        }

        stage('Prepare Python Env') {
            steps {
                // 在当前 Jenkins 工作区创建虚拟环境并安装依赖
                // 用相对路径，不依赖任何个人电脑的绝对路径
                bat '''
                    chcp 65001
                    python -m venv .venv
                    .venv\\Scripts\\python.exe -m pip install --upgrade pip
                    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Auto Tests') {
            steps {
                // 强制 UTF-8，防止控制台打印 Emoji 报错
                withEnv(['PYTHONIOENCODING=utf-8']) {
                    bat '''
                        chcp 65001
                        .venv\\Scripts\\python.exe -m pytest -sv
                    '''
                }
            }
        }
    }

    post {
        always {
            // 可选：测试生成了 JUnit 报告再放开
            junit 'reports/results.xml'

            // 构建结束后清理工作区，释放磁盘空间
            // cleanWs()
        }
    }
}
