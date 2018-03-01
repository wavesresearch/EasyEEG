from ..default import *
from .. import structure
from .basic import * 
from ..statistics import stats_methods

from scipy.spatial.distance import cosine # 1-cosD

def calc_cosD(df): # df: channel,subject,condition_group
    cond_A, cond_B = [average(conditon_group_data, keep='channel').mean(axis=1) 
        for conditon_group_id,conditon_group_data in df.groupby(level='condition_group')]
    return cosine(cond_A, cond_B)

def sub_func(group_data, shuffle=500, within_subject=True):
    result_real = calc_cosD(group_data)
    dist_baseline = []
    for _ in range(shuffle):
        shuffle_on_level(group_data, 'condition_group', within_subject=within_subject)
        dist_baseline.append(calc_cosD(group_data))

    pvalue = stats_methods.get_pvalue_from_distribution(result_real, dist_baseline)
    return pvalue, result_real

# def sub_func4(group_data):
#             result_real = []
#             baseline = []
#             for subject_group_id,subject_group_data in group_data.groupby(level='subject'):
#                 result_real.append(calc_cosD(subject_group_data))
#                 dist_baseline = []
#                 for _ in range(shuffle):
#                     shuffle_on_level(group_data, 'condition_group')
#                     dist_baseline.append(calc_cosD(group_data))
#                 baseline.append(np.mean(dist_baseline))

#             pvalue = scipy.stats.ttest_rel(result_real, baseline)[1]
#             return pvalue, result_real

def tanova(self,step_size='1ms',win_size='1ms',sample='mean',shuffle=500,mode=1,parallel=False):
    # with the decorator, we can just focuse on case data instead of batch/collection data
    @self.iter('all')
    def to_tanova1(case_raw_data):
        case_raw_data = sampling(case_raw_data, step_size, win_size, sample)
        check_availability(case_raw_data, 'condition_group', 2)
        return roll_on_levels(case_raw_data, sub_func, arguments_dict=dict(shuffle=shuffle, within_subject=False), levels='time', prograssbar=True, parallel=parallel)

    @self.iter('all')
    def to_tanova2(case_raw_data):
        case_raw_data = sampling(case_raw_data, step_size, win_size, sample)
        check_availability(case_raw_data, 'condition_group', 2)
        return roll_on_levels(case_raw_data, sub_func, arguments_dict=dict(shuffle=shuffle, within_subject=True), levels='time', prograssbar=True, parallel=parallel)

    @self.iter('average')
    def to_tanova3(case_raw_data):
        case_raw_data = sampling(case_raw_data, step_size, win_size, sample)
        check_availability(case_raw_data, 'condition_group', 2)
        return roll_on_levels(case_raw_data, sub_func, arguments_dict=dict(shuffle=shuffle, within_subject=True), levels='time', prograssbar=True, parallel=parallel)

    if mode==1:
        tanova_collection, annotation_collection = to_tanova1()
    elif mode==2:
        tanova_collection, annotation_collection = to_tanova2()
    elif mode==3:
        tanova_collection, annotation_collection = to_tanova3()

    default_plot_params = dict(title='TANOVA',plot_type=['direct','heatmap'], x_len=12, re_assign=[(0,0.01,0.05,0.1,1),(4,3,2,1)],
                                color=sns.cubehelix_palette(light=1, as_cmap=True), grid=True,
                                x_title='time', y_title='condition_group',cbar_title='pvalue',cbar_values=['>0.1','<0.1','<0.05','<0.01'])

    return structure.Analyzed_data('TANOVA', tanova_collection, annotation_collection, default_plot_params=default_plot_params)

def cosine_distance_dynamics(self):
    # with the decorator, we can just focuse on case data instead of batch/collection data
    @self.iter('average')
    def calc(case_raw_data):
        check_availability(case_raw_data, 'condition_group', 2)
        return roll_on_levels(case_raw_data, calc_cosD, levels='time')

    cosine_distance_collection = calc()

    default_plot_params = dict(title='cosine_distance_dynamics', plot_type=['direct','waveform'], x_title='time', y_title='distance', color="Set1", style='darkgrid')
    return structure.Analyzed_data('cosine distance dynamics', cosine_distance_collection, default_plot_params=default_plot_params)


# def Topo_CosD(data,container,step='1ms',err_style='ci_band',win='5ms',sample='mean', sig_limit=0):

#     def calc(batch_data):

#         def sub_task(scene_data):
#             scene_data = mean_axis(scene_data,'trial')
#             # sampling along time axis
#             if step!='1ms':
#                 scene_data = point_sample(scene_data,step)
#             elif win!='1ms':
#                 scene_data = window_sample(scene_data,win,sample)

#             distance = process.row_roll(scene_data, row=['subject','condition','time'], column=['channel'], func=calc_cosD)

#             return distance['p'].unstack('time')

#         map_result = [(scene_name,sub_task(scene_data)) for scene_name,scene_data in batch_data]

#         result = pd.concat([result for name,result in map_result])
#         result.sort_index(inplace=True)
#         result = result.reindex([name for name,result in map_result],level='condition') # 使condition的顺序和定义时一致

#         return result

#     # group the data
#     container_data = group.extract(data,container,'Topograph')
#     # calculate
#     diff_data = [(title,calc(batch_data)) for title,batch_data in container_data]
#     diff_stat_data = [None for i in diff_data]

#     # plot
#     note = ['Time(ms)','Distance',[]]
#     plot_put.block(diff_data,note,err_style,diff_stat_data,win,sig_limit=0)

#     return diff_data, diff_stat_data