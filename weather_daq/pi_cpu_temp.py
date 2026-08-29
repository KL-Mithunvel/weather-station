import subprocess

from daq_log import logger


class PiBoard:

    @classmethod
    def read_cpu_temp(cls):
        cmd = ['/usr/bin/vcgencmd', 'measure_temp']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                logger.error(f'vcgencmd exited {res.returncode}: {res.stderr.strip()}')
                return None
            output = str(res.stdout)
            return float(output[output.find('=') + 1:].rstrip("'C\n"))
        except (OSError, subprocess.SubprocessError, IndexError, ValueError) as e:
            logger.error(f'CPU temperature read failed: {e}')
            return None


if __name__ == "__main__":
    print(f'{PiBoard.read_cpu_temp()}oC')
