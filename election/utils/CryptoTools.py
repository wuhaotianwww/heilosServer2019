from Crypto.Math.Numbers import *
from Crypto import Random
from Crypto.PublicKey import ElGamal
from Crypto.Hash import SHA256, SHA512
import json


class GenerateParameters(object):
    def __init__(self, length):
        self.key = ElGamal.generate(length, Random.new().read)
        self.p = self.key.p
        self.g = self.key.g
        self.h = self.key.y
        self.x = self.key.x

    def get_public_key(self):
        dic = {'g': str(self.g), 'h': str(self.h), 'p': str(self.p)}
        return str(dic)

    def get_private_key(self):
        return str(self.x)


class RandomGen(object):
    def __init__(self, bound):
        self.p = bound

    def get_random_int(self):
        return Integer.random_range(min_inclusive=2, max_exclusive=self.p, randfunc=Random.new().read)


class HashTools(object):
    def __init__(self, length):
        if length > 300:
            self.h = SHA512.new()
        else:
            self.h = SHA256.new()

    def get_hash(self, mybytes):
        self.h.new(mybytes)
        return str(self.h.digest())


class MixByHash(object):
    @staticmethod
    def generate_random_sequence(pi, length):
        """根据输入参数 生成随机打乱后的新坐标"""
        verify_list = []
        new_sequence = []
        h = SHA256.new()
        for i in range(length):
            verify_list.append(-1)
        for i in range(length):
            h.new(pi.to_bytes() + i.to_bytes(8, byteorder="big"))
            byte = h.digest()
            m = int(Integer.__mod__(Integer(Integer.from_bytes(byte)), Integer(length)))
            if verify_list[m] == -1:
                new_sequence.append(m)
                verify_list[m] = 0
            else:
                m = (m+1) % length
                while verify_list[m] != -1:
                    m = (m+1) % length
                new_sequence.append(m)
                verify_list[m] = 0
        del h
        return new_sequence

    @staticmethod
    def generate_random_case(g, y, p):
        """根据输入产生80个随机的0/1情况"""
        case_list = []
        length = 10
        h = SHA256.new()
        h.update(g.to_bytes() + y.to_bytes() + p.to_bytes())
        byte = h.digest()
        for i in range(length):
            for j in range(8):
                if byte[i] & (0x01 << j):
                    case_list.append(True)
                else:
                    case_list.append(False)
        del h
        return case_list

    @staticmethod
    def generate_sequence_difference(pi1, pi2, length):
        """生成两个参数下位置   的 相对关系"""
        new_sequence = []
        for i in range(length):
            new_sequence.append(-1)
        new_sequence_1 = MixByHash.generate_random_sequence(pi1, length)
        new_sequence_2 = MixByHash.generate_random_sequence(pi2, length)
        for i in range(length):
            new_sequence[new_sequence_1[i]] = new_sequence_2[i]
        return new_sequence


class MCipher(object):
    @staticmethod
    def generate_secrete_file(vote, votegr, vote_num, Pi, R, g, h, p, x):
        """根据已知参数生成加密后的密文"""
        cipher = []
        gr = []
        hr = []

        # 初始化list
        num = len(vote[0])
        for i in range(vote_num):
            cipher.append([Integer(i) for i in range(num)])
            gr.append([Integer(i) for i in range(num)])
            hr.append([Integer(i) for i in range(num)])

        # 计算哈希打乱之后的位置
        position = MixByHash.generate_random_sequence(Pi, vote_num)

        # 生成密文
        for i in range(vote_num):
            for j in range(num):
                cipher[position[i]][j] = Integer.__mod__((pow(g, R[i], p) * vote[i][j] * pow(h, R[i], p)), p)
                gr[position[i]][j] = Integer.__mod__(pow(g, R[i], p) * votegr[i][j], p)
                hr[position[i]][j] = Integer.__mod__(pow(h, R[i], p) * pow(votegr[i][j], x, p), p)

        return cipher, gr, hr

    @staticmethod
    def random_sample(p):
        return Integer.random_range(min_inclusive=2, max_exclusive=p, randfunc=Random.new().read)

    @staticmethod
    def random_list(length, p):
        return [MCipher.random_sample(p) for i in range(length)]


class MixNet(object):
    def __init__(self, p, g, private_key, public_key, vote, votegr, vote_num, selections):
        self.p = p
        self.g = g
        self.vote = vote
        self.votegr = votegr
        self.vote_num = vote_num
        self.private_key = private_key
        self.public_key = public_key
        self._Pi = MCipher.random_sample(self.p)
        self._R0 = MCipher.random_list(self.vote_num, self.p)
        self.selections = selections

    def ciphertext_generate(self):
        return MCipher.generate_secrete_file(self.vote, self.votegr, self.vote_num, self._Pi, self._R0,
                                             self.g, self.public_key, self.p, self.private_key)

    def get_mes(self, encoder, i):
        for key, value in self.selections[i].items():
            if pow(self.g, value, self.p) == encoder:
                return key

    def get_plain_message(self):
        message = []
        num = len(self.vote[0])
        for i in range(self.vote_num):
            message.append(["0" for j in range(num)])
        position = MixByHash.generate_random_sequence(self._Pi, self.vote_num)
        for i in range(self.vote_num):
            for j in range(num):
                gm = Integer.__mod__(self.vote[i][j] * Integer.inverse(self.votegr[i][j], self.p) * Integer.inverse(pow(self.votegr[i][j], self.private_key, self.p), self.p), self.p)
                message[position[i]][j] = self.get_mes(gm, j)
        return message

    def _generate_verify_case(self, case):
        """根据不同的case输出不同的验证信息"""
        pii = MCipher.random_sample(self.p)
        R = MCipher.random_list(self.vote_num, self.p)
        cipher, gr, hr = MCipher.generate_secrete_file(self.vote, self.votegr, self.vote_num, pii, R, self.g, self.public_key, self.p, self.private_key)
        if case:
            difference = []
            for i in range(self.vote_num):
                difference.append({"sign": '+', "value": Integer(0)})
            sequence_differnce = MixByHash.generate_sequence_difference(self._Pi, pii, self.vote_num)
            origin_sequence = MixByHash.generate_random_sequence(self._Pi, self.vote_num)
            for i in range(self.vote_num):
                if R[i] >= self._R0[i]:
                    difference[origin_sequence[i]] = {"sign": '+', "value": R[i]-self._R0[i]}
                else:
                    difference[origin_sequence[i]] = {"sign": '-', "value": self._R0[i]-R[i]}
            return cipher, gr, hr, sequence_differnce, difference
        else:
            return cipher, gr, hr, pii, R

    def verify_file_generate(self, file_path):
        """生成密文展示结果"""
        result_file = []
        encoder, grr, hrr = self.ciphertext_generate()
        plaintxt = self.get_plain_message()
        for i in range(self.vote_num):
            dic = {}
            dic['encoder'] = [str(a.to_bytes().hex()) for a in encoder[i]]
            dic['grr'] = [str(a.to_bytes().hex()) for a in grr[i]]
            dic['hrr'] = [str(a.to_bytes().hex()) for a in hrr[i]]
            dic['plaintxt'] = [a for a in plaintxt[i]]
            result_file.append(dic)

        """生成验证文件"""
        verify_file = []
        case_list = MixByHash.generate_random_case(self.p, self.p, self.p)
        for each in case_list:
            if each:
                cipher, gr, hr, sequence_difference, difference = self._generate_verify_case(each)
                verify_file.append({'cipher': [[str(a.to_bytes().hex()) for a in item] for item in cipher],
                                    'gr': [[str(a.to_bytes().hex()) for a in item] for item in gr],
                                    'hr': [[str(a.to_bytes().hex()) for a in item] for item in hr],
                                    'case': each,
                                    'sequence_difference': sequence_difference,
                                    'difference': [str(item["sign"])+str(item["value"].to_bytes().hex()) for item in difference]})
            else:
                cipher, gr, hr, pii, R = self._generate_verify_case(each)
                verify_file.append({'cipher': [[str(a.to_bytes().hex()) for a in item] for item in cipher],
                                    'gr': [[str(a.to_bytes().hex()) for a in item] for item in gr],
                                    'hr': [[str(a.to_bytes().hex()) for a in item] for item in hr],
                                    'case': each, 'Pi': str(pii.to_bytes().hex()),
                                    'rand': [str(item.to_bytes().hex()) for item in R]})

        # 写入文件
        with open(file_path, 'w') as f:
            json.dump(result_file, f)
            json.dump(verify_file, f)


def str2integer(integer_string):
    """字符串转大整数"""
    num = Integer(0)
    length = len(integer_string)
    for i in range(length):
        num += Integer.__mul__(Integer.__pow__(Integer(10), Integer(length-i-1)), Integer(int(integer_string[i])))
    return num


if __name__ == '__main__':
    vote_number = 5
    write_len = 100
    mykey = GenerateParameters(256)
    dic = eval(mykey.get_public_key())
    g = str2integer(dic['g'])
    h = str2integer(dic['h'])
    p = str2integer(dic['p'])
    x = str2integer(mykey.get_private_key())
    print(x)
    # myvote = []
    # vote0 = myvote.generate()
    # vote_integer = []
    hashvalue = [{"早餐": str2integer("681768140220463028835442241"),
                 "午餐": str2integer("4224177175208842725333075"),
                 "晚餐": str2integer("709832358520091555620564")}]

    # m = covert_str2integer("681768140220463028835442241")
    # r = MCipher.random_sample(p)
    # gm = pow(g, m, p)
    # print(gm)
    # vote = Integer.__mod__(pow(g, (r + m), p) * pow(h, r, p), p)
    # gr = pow(g, r, p)
    # hr = pow(h, r, p)
    # vr = Integer.__mod__(vote * Integer.inverse(hr, p) * Integer.inverse(gr, p), p)
    # print(vr)
    R = MCipher.random_list(5, p)
    m = [[str2integer("681768140220463028835442241"), str2integer("4224177175208842725333075"), str2integer("709832358520091555620564")]]
    vote = [[Integer.__mod__(pow(g, (r + m[0][0]), p)*pow(h, r, p), p)] for r in R]
    votegr = [[pow(g, r, p)] for r in R]
    mymix = MixNet(p, g, x, h, vote, votegr, len(vote), hashvalue)
    print(mymix.ciphertext_generate())
    print(mymix.get_plain_message())
    mymix.verify_file_generate("liscen.json")