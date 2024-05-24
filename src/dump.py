from itertools import product , combinations
import numpy as np

def flatten_prod(prod):
    """

    """
    result = []
    for outer_tuple in prod:
        inner_list = []
        for item in outer_tuple:
            index, array_value = item
            inner_list.append(index)
            inner_list.append(array_value.item()) 
        result.append(inner_list)
    return result

# Da pra generalizar pra k arrays, aqui so funciona pra 2
# O jeito besta de fazer isso e fazer dois a dois

class CartesianProduct():
    def __init__(self,arrs : list) -> None:
        self.data = self.order_cartersian(*arrs)

        
# Aqui o elemento z[i,j] é ordenado representa o elemento i do arr_1 e o elemento j do arr_2
    @staticmethod
    def order_cartersian(arr_1 , arr_2 ):
        m = arr_1.shape[0]
        n = arr_2.shape[0]

        arr_1 = [e for e in enumerate(arr_1)]
        arr_2 = [e for e in enumerate(arr_2)]


        prod = np.array(list(product(arr_1 , arr_2)))
        prod = prod.reshape(m*n,4)

        # Provalmente funciona dizer que z[i] = prod[n*i -1 :n*(i+1) + 1] , acho que prod é ordenado
        z = np.empty(shape=(m,n,2))

        for i in range (m) :
            for j in range(n):
                mask = (prod[: , 0] == i) & (prod[: , 2] == j)
                e = prod[mask][0,[1,3]]  
                z[i,j] = e
        # Aqui o elemento z[i,j] é ordenado representa o elemento i do arr_1 e o elemento j do arr_2
        return z


k = 4

arrs = [np.random.rand(np.random.randint(50),1).flatten() for i in range(k)]

z = np.empty(shape=(k,k), dtype=object)

combs = list(combinations(enumerate(arrs) , 2))

for iter in range(len(combs)):
    idx_i = combs[iter][0][0]
    a_i = combs[iter][0][1]
    idx_j = combs[iter][1][0]
    a_j = combs[iter][1][1]
    z[idx_i , idx_j] = CartesianProduct([a_i ,a_j])

pass
# Aqui o elemento z[i,j].data[m,n] representa -> prod cartesiano do arr_i com o arr_j na ordem do vetor arrs , elemento m de arr_i com elemento n de a_j
# z é uma matriz triagular superior , com diagonal 0
# Nao parece mt lento mas é a abordagem trogolodita , da pra vetorizar e usar uns fors a menos na mask provavelmente, mas tem que pensa um pouco

