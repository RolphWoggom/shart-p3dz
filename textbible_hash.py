# ported from FeLanguage::GetHash(char const *) found at 0x0030f0b0 in the ps2 prototype
def textbible_hash(string, modulo=0x2DA027):
    hash_ = 0
    for i in range(len(string)):
        hash_ = ((hash_ * 0x40) + ord(string[i])) % modulo
    return hash_
