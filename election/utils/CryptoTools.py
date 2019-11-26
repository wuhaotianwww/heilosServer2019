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


class Hash256Tools(object):
    def __init__(self, length):
        if length > 300:
            self.h = SHA512.new()
        else:
            self.h = SHA256.new()

    def get_hash(self, mybytes):
        self.h.new(mybytes)
        return self.h.digest()


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
    def generate_random_ex(H, Gn):
        """根据输入产生160bit参数x,e"""
        h = SHA256.new()
        h.new(H.x.to_bytes()+Gn[0].x.to_bytes()+Gn[1].x.to_bytes()+Gn[2].x.to_bytes())
        byte = h.digest()
        x = (Integer.from_bytes(byte)) % (pow(2, 160))
        h.new(H.y.to_bytes() + Gn[0].y.to_bytes() + Gn[1].y.to_bytes() + Gn[2].y.to_bytes())
        byte = h.digest()
        e = (Integer.from_bytes(byte)) % (pow(2, 160))
        del h
        return x, e

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
    def generate_secrete_file(vote, vote_num, Pi, R, g, h, p):
        """根据已知参数生成加密后的密文"""
        cipher = []
        gr = []
        hr = []

        # 初始化list
        for i in range(vote_num):
            cipher.append(Integer(0))
            gr.append(Integer(0))
            hr.append(Integer(0))

        # 计算哈希打乱之后的位置
        position = MixByHash.generate_random_sequence(Pi, vote_num)

        # 生成密文
        for i in range(vote_num):
            cipher[position[i]] = Integer.__mod__((pow(g, R[i], p) * vote[i] * pow(h, R[i], p)), p)
            gr[position[i]] = pow(g, R[i], p)
            hr[position[i]] = pow(h, R[i], p)

        return cipher, gr, hr

    @staticmethod
    def random_sample(p):
        return Integer.random_range(min_inclusive=2, max_exclusive=p, randfunc=Random.new().read)

    @staticmethod
    def random_list(length, p):
        return [MCipher.random_sample(p) for i in range(length)]


class MixNet(object):
    def __init__(self, p, g, private_key, public_key, vote, vote_num):
        self.p = p
        self.g = g
        self.vote = vote
        self.vote_num = vote_num
        self.private_key = private_key
        self.public_key = public_key
        self._Pi = MCipher.random_sample(self.p)
        self._R0 = MCipher.random_list(self.vote_num, self.p)

    def ciphertext_generate(self):
        return MCipher.generate_secrete_file(self.vote, self.vote_num, self._Pi, self._R0,
                                             self.g, self.public_key, self.p)

    def _generate_verify_case(self, case):
        """根据不同的case输出不同的验证信息"""
        pii = MCipher.random_sample(self.p)
        R = MCipher.random_list(self.vote_num, self.p)
        cipher = MCipher.generate_secrete_file(self.vote, self.vote_num, pii, R, self.g, self.public_key, self.p, self.is_curve )
        if case:
            pass
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
            return cipher, sequence_differnce, difference
        else:
            return cipher, pii, R

    def verify_file_generate(self, file_path):
        """生成验证文件"""
        verify_file = []
        case_list = MixByHash.generate_random_case(self.p, self.p, self.p)
        for each in case_list:
            if each:
                pass
                cipher, sequence_difference, difference = self._generate_verify_case(each)
                verify_file.append({'cipher': [str(item.to_bytes().hex()) for item in cipher], 'case': each,
                                    'sequence_difference': sequence_difference,
                                    'difference': [str(item["sign"])+str(item["value"].to_bytes().hex()) for item in difference]})
            else:
                cipher, pii, R = self._generate_verify_case(each)
                verify_file.append({'cipher': [str(item.to_bytes().hex()) for item in cipher],
                                    'case': each, 'Pi': str(pii.to_bytes().hex()),
                                    'rand': [str(item.to_bytes().hex()) for item in R]})

        # 写入文件
        with open(file_path, 'w') as f:
            json.dump(verify_file, f)

