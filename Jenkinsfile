node {
    checkout scm;

    try {
        slack();
        ansiColor('xterm') {
            stage('Build') {
                echo 'Building docker images...';
                sh 'make build';
            }
            stage('Lint') {
                echo 'Lint ...';
                sh 'make lint';
            }
        }
        slack('SUCCESS')
    } catch (err) {
        slack('FAILURE');
        throw err;
    }
}
