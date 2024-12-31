import subprocess


class PiBoard:

    @classmethod
    def read_cpu_temp(cls):
        temp = None
        cmd = ['/usr/bin/vcgencmd', 'measure_temp']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                output = str(res.stdout)
                temp = float(output[output.find('=')+1:].rstrip("'C\n"))
            return temp
        except (OSError, FileNotFoundError, IndexError, ValueError) as e:
            print(e)
            return None


if __name__ == "__main__":
    print(f'{PiBoard.read_cpu_temp()}oC')
