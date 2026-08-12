pipeline {
    // 在您的 Windows Jenkins 节点上运行
    agent any

    stages {
        stage('Run Auto Tests') {
            steps {
                // 强制使用 UTF-8 编码，防止控制台打印 Emoji 报错
                withEnv(['PYTHONIOENCODING=utf-8']) {
                    bat 'chcp 65001 && C:\\Users\\NotAfraidofFailure\\WorkBuddy\\2026-08-07-12-55-14\\SauceDemo_autotest\\.venv\\Scripts\\python.exe -m pytest -sv'
                }
            }
        }
    }

    // post {
    //     always {
    //         // 注意：目前您的测试大概率还没生成 'reports/results.xml' 这个文件
    //         // 如果此时配置 junit，Jenkins 可能会报“文件不存在”的错
    //         // 建议先注释掉这一行，等测试成功生成报告后再放开
<<<<<<< HEAD
    //        junit 'reports/results.xml'
    //     }
    // }
}

}
=======
    //         junit 'reports/results.xml' 
    //     }
    // }
}
>>>>>>> 3b0fdb9e8f74ab34f4a0f7753199eb6bcc2986f9
