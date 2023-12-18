pathways = []
alignments = []


def waterman(seq1, seq2):
    global sequence_1
    global sequence_2
    global matrix
    global matrix_row
    global matrix_column
    sequence_1 = seq1
    sequence_2 = seq2
    matrix_row = len(sequence_1) + 1
    matrix_column = len(sequence_2) + 1
    matrix = [[[[None] for i in range(2)] for i in range(matrix_column)] for i in range(matrix_row)]

    i, j = scoring(1, -1, -1)

    max = 0
    for k in range(1, matrix_row):
        for m in range(1, matrix_column):
            max = matrix[k][m][0] if matrix[k][m][0] > max else max

    while (i >= 0) and (j >= 0):
        if matrix[i][j][0] == max:
            k = i
            m = j
            tot_aln = find_pathways(k, m)
            print('Total Number of Alignments - Waterman:', tot_aln)
            traceback(k, m)
        i = i - 1
        j = j - 1


def scoring(match, mismatch, gap):
    global match_score
    global mismatch_score
    global gap_penalty

    match_score = match
    mismatch_score = mismatch
    gap_penalty = gap

    for i in range(matrix_row):
        matrix[i][0] = [0 * i, []]
    for j in range(matrix_column):
        matrix[0][j] = [0 * j, []]

    for i in range(1, matrix_row):
        for j in range(1, matrix_column):
            score = match_score if (sequence_1[i - 1] == sequence_2[j - 1]) else mismatch_score
            l_val = matrix[i][j - 1][0] + gap_penalty
            d_val = matrix[i - 1][j - 1][0] + score
            t_val = matrix[i - 1][j][0] + gap_penalty
            val = [l_val, d_val, t_val]
            max_val = max(val)
            if max_val < 0:
                max_val = 0
            matrix[i][j] = [max_val, [i + 1 for i, v in enumerate(val) if v == max_val]] # 1 for left, 2 for diagonal, 3 for top
    return i, j


def find_pathways(ii, jj, path=''): # Recursive function to find the possible best pathways
    global pathways
    i = ii
    j = jj
    if (i == 0 and j == 0) or (matrix[i][j][0] == 0):
        pathways.append(path)
        return 2
    dir_n = len(matrix[i][j][1]) # Number of paths possible from the current element
    while dir_n <= 1:
        num_dir = matrix[i][j][1][0] if (i != 0 and j != 0) else (1 if i == 0 else (3 if j==0 else 0)) #Direction of the arrows
        path = path + str(num_dir)
        if num_dir == 1: # Left
            j = j - 1
        elif num_dir == 2: # Diagonal
            i = i-1
            j = j-1
        elif num_dir == 3: # Top
            i = i-1
        dir_n = len(matrix[i][j][1])
        if (i == 0 and j == 0) or (matrix[i][j][0] == 0):
            pathways.append(path)
            return 1
    if dir_n > 1:
        for k in range(dir_n):
            num_dir = matrix[i][j][1][k] if (i != 0 and j != 0) else (1 if i == 0 else (3 if j == 0 else 0))
            temp_path = path + str(num_dir)
            if num_dir == 1: # Left
                n_i = i
                n_j = j-1
            elif num_dir == 2: # Diagonal
                n_i = i-1
                n_j = j-1
            elif num_dir == 3: # Top
                n_i = i-1
                n_j = j
            find_pathways(n_i, n_j, temp_path) # Calls itself
    return len(pathways)


def traceback(ii, jj):
    global alignments
    count = 0 # Alignment count
    for elem in pathways: # Go through the list pathways
        i = ii - 1
        j = jj - 1
        left_aln = ''
        top_aln = ''
        step = 0
        aln_info = []
        for k in range(len(elem)): # Go through each element in the list pathways
            n_dir = elem[k]
            score = matrix[i + 1][j + 1][0]
            step = step + 1
            aln_info.append([step, score, n_dir])
            if n_dir == '2':
                left_aln = left_aln + sequence_1[i]
                top_aln = top_aln + sequence_2[j]
                i = i - 1
                j = j - 1
            elif n_dir == '1':
                left_aln = left_aln + '-'
                top_aln = top_aln + sequence_2[j]
                j = j - 1
            elif n_dir == '3':
                left_aln = left_aln + sequence_1[i]
                top_aln = top_aln + '-'
                i = i - 1
        count = count + 1
        alignments.append([top_aln[::-1], left_aln[::-1], elem, aln_info, count])
    print_aligments(alignments)


def print_aligments(alignments): #Function to print the alignments
    for elem in alignments:
        print(elem[0]+'\n'+elem[1]+'\n')



waterman('ACATAG','AATG')