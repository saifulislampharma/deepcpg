from predict.models.dnn.model import *
from keras.activations import sigmoid, relu
from keras.optimizers import SGD


def test_params():
    p = Params()
    p.cpg.drop_in = 0.0
    p.cpg.drop_out = 0.5
    p.seq.update({'num_hidden': 0, 'batch_norm': True,
                  'optimizer_params': {'lr': 0.5}})
    print(p)


def test_seq():
    p = Params()
    p.cpg = False

    p.seq = SeqParams()
    pc = p.seq
    pc.activation = 'sigmoid'
    pc.num_hidden = 5
    pc.drop_in = 0.5
    pc.drop_out = 0.1
    pc.batch_norm = True
    pc.num_filters = 1
    pc.filter_len = 2
    pc.pool_len = 4

    p.target.num_hidden = 0
    m = build(p, ['u0', 'u1'], seq_len=10, compile=False)
    assert 'u0_y' in m.output_order
    assert 'u1_y' in m.output_order
    assert 's_x' in m.input_order
    assert 's_h1b' in m.nodes.keys()
    assert m.nodes['s_h1d'].p == pc.drop_out
    assert m.nodes['s_xd'].p == pc.drop_in
    assert m.nodes['s_h1a'].activation is sigmoid
    t = m.nodes['s_c1']
    assert t.filter_length == pc.filter_len
    assert t.nb_filter == pc.num_filters


def test_cpg():
    p = Params()
    p.seq = False

    p.cpg = CpgParams()
    pc = p.cpg
    pc.activation = 'sigmoid'
    pc.num_hidden = 5
    pc.drop_in = 0.5
    pc.drop_out = 0.1
    pc.batch_norm = True
    pc.num_filters = 1
    pc.filter_len = 2
    pc.pool_len = 4

    p.target.num_hidden = 0

    m = build(p, ['u0', 'u1'], cpg_len=10, compile=False)
    assert 'u0_y' in m.output_order
    assert 'u1_y' in m.output_order
    assert 'c_x' in m.input_order
    assert 'c_h1b' in m.nodes.keys()
    assert m.nodes['c_h1d'].p == pc.drop_out
    assert m.nodes['c_xd'].p == pc.drop_in
    assert m.nodes['c_h1a'].activation is sigmoid
    t = m.nodes['c_c1']
    assert t.nb_filter == pc.num_filters
    assert t.nb_row == 1
    assert t.nb_col == pc.filter_len


def test_joint():
    p = Params()
    p.seq = SeqParams()
    p.seq.num_hidden = 2
    p.seq.activation = 'relu'
    p.seq.drop_in = 0.1
    p.seq.drop_out = 0.5
    p.seq.batch_norm = False
    p.seq.filter_len = 3
    p.seq.num_filter = 1

    p.cpg = CpgParams()
    p.cpg.num_hidden = 3
    p.cpg.activation = 'sigmoid'
    p.cpg.drop_in = 0.0
    p.cpg.drop_out = 0.0
    p.cpg.batch_norm = True
    p.cpg.filter_len = 4
    p.cpg.num_filter = 2

    p.target = TargetParams()
    p.target.activation = 'sigmoid'
    p.target.num_hidden = 2
    p.target.drop_out = 0.0
    p.target.batch_norm = True

    p.optimizer = 'sgd'
    p.optimizer_params = {'lr': 0.05}

    targets = ['u0', 'u1']
    m = build(p, targets, seq_len=10, cpg_len=5, compile=True)

    n = m.nodes

    for target in targets:
        def label(x):
            return '%s_%s' % (target, x)
        assert label('y') in m.output_order
        assert n[label('o')].activation is sigmoid
        assert label('h1d') not in n.keys()
        assert label('h1b') in n.keys()

    assert n['s_xd'].p == p.seq.drop_in
    assert n['s_f1d'].p == p.seq.drop_out
    assert n['s_h1d'].p == p.seq.drop_out
    assert n['s_c1'].activation is relu
    assert n['s_c1'].nb_filter is p.seq.num_filters
    assert n['s_c1'].filter_length is p.seq.filter_len
    assert n['s_h1a'].activation is relu

    assert 'c_xd' not in n.keys()
    assert 'c_h1d' not in n.keys()
    assert n['c_c1'].activation is sigmoid
    assert n['c_c1'].nb_filter is p.cpg.num_filters
    assert n['c_c1'].nb_row == 1
    assert n['c_c1'].nb_col is p.cpg.filter_len
    assert n['c_h1a'].activation is sigmoid

    assert isinstance(m.optimizer, SGD)
    assert round(float(m.optimizer.lr.get_value()), 3) == p.optimizer_params['lr']
