import os
import librosa
import librosa.display
import matplotlib.pyplot as plt

def plot_spec(spec, label):
    # 绘制语谱图
    plt.figure(figsize=(8, 8))
    plt.imshow(spec, aspect='auto', origin='lower')
    # librosa.display.specshow(spectrogram, sr=sample_rate, x_axis='time', y_axis='hz')
    # plt.colorbar(format='%+2.0f dB')

    # plt.xticks([0, 160, 320, 480, 640, 800, 960, 1120], ['0', '0.5', '1.0', '1.5', '2.0', '2.5', '3.0', '3.5'], fontproperties = 'Times New Roman', size = 28)
    # plt.yticks([0, 256, 512, 1024], ['0', '2', '4', '8'], fontproperties = 'Times New Roman', size = 28)
    # plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 36})
    # plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman', 'size': 36})
    plt.xticks([])  # 去掉x轴
    plt.yticks([])  # 去掉y轴
    plt.axis('off')  # 去掉坐标轴
    plt.tight_layout()
    plt.savefig(label + '.png', dpi=100)


def plot_multi_spec(spec_1, spec_2, spec_3, spec_4, spec_5):
    # 绘制语谱图
    fig = plt.figure(figsize=(10, 2))
    # plt.subplots_adjust(wspace=0.06, hspace=0.05)
    height = 1

    axe1 = fig.add_subplot(151)
    axe1.set_title("Natural Noisy", fontdict={'family': 'Times New Roman'}, fontsize=10, y=height)
    plt.imshow(spec_1, aspect='auto', origin='lower')
    plt.xticks([0, 160, 320, 480, 640, 800], ['0', '0.5', '1.0', '1.5', '2.0', '2.5'], fontproperties = 'Times New Roman', size = 8)
    plt.yticks([0, 256, 512, 768, 1024], ['0', '2', '4', '6', '8'], fontproperties = 'Times New Roman', size = 8)
    plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 8})
    plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman', 'size': 8})

    axe2 = fig.add_subplot(152)
    axe2.set_title("Natural Clean", fontdict={'family': 'Times New Roman'}, fontsize=10, y=height)
    plt.imshow(spec_2, aspect='auto', origin='lower')
    plt.xticks([0, 160, 320, 480, 640, 800], ['0', '0.5', '1.0', '1.5', '2.0', '2.5'], fontproperties = 'Times New Roman', size = 8)
    plt.yticks([0, 256, 512, 768, 1024], ['0', '2', '4', '6', '8'], fontproperties = 'Times New Roman', size = 8)
    plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 8})
    # plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman'})

    axe3 = fig.add_subplot(153)
    axe3.set_title("CMGAN", fontdict={'family': 'Times New Roman'}, fontsize=10, y=height)
    plt.imshow(spec_3, aspect='auto', origin='lower')
    plt.xticks([0, 160, 320, 480, 640, 800], ['0', '0.5', '1.0', '1.5', '2.0', '2.5'], fontproperties = 'Times New Roman', size = 8)
    plt.yticks([0, 256, 512, 768, 1024], ['0', '2', '4', '6', '8'], fontproperties = 'Times New Roman', size = 8)
    plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 8})
    # plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman'})

    axe4 = fig.add_subplot(154)
    axe4.set_title("MP-SENet (Conformer)", fontdict={'family': 'Times New Roman'}, fontsize=10, y=height)
    plt.imshow(spec_4, aspect='auto', origin='lower')
    plt.xticks([0, 160, 320, 480, 640, 800], ['0', '0.5', '1.0', '1.5', '2.0', '2.5'], fontproperties = 'Times New Roman', size = 8)
    plt.yticks([0, 256, 512, 768, 1024], ['0', '2', '4', '6', '8'], fontproperties = 'Times New Roman', size = 8)
    plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 8})
    # plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman'})
    # librosa.display.specshow(spectrogram, sr=sample_rate, x_axis='time', y_axis='hz')
    # plt.colorbar(format='%+2.0f dB')

    axe4 = fig.add_subplot(155)
    axe4.set_title("MP-SENet (Transformer)", fontdict={'family': 'Times New Roman'}, fontsize=10, y=height)
    plt.imshow(spec_5, aspect='auto', origin='lower')
    plt.xticks([0, 160, 320, 480, 640, 800], ['0', '0.5', '1.0', '1.5', '2.0', '2.5'], fontproperties = 'Times New Roman', size = 8)
    plt.yticks([0, 256, 512, 768, 1024], ['0', '2', '4', '6', '8'], fontproperties = 'Times New Roman', size = 8)
    plt.xlabel('Time(s)', fontdict={'family': 'Times New Roman', 'size': 8})
    # plt.ylabel('Frequency(kHz)', fontdict={'family': 'Times New Roman'})
    # librosa.display.specshow(spectrogram, sr=sample_rate, x_axis='time', y_axis='hz')
    # plt.colorbar(format='%+2.0f dB')

    plt.tight_layout()
    plt.savefig('D:/BaiduNetdiskDownload/specs_reply_2.2.pdf', bbox_inches='tight', pad_inches=0, dpi=600)
    print("图片保存路径：", os.path.abspath('enhanced.png'))


# 读取音频文件
def main():
    sampling_rate = 16000
    audio_path = r'C:/Users/CHENJINHAN/Desktop/mid/hdns-ap_desktop-Headset_Microphone_Plantronics_Blackwire_3220_Series-pid_900119-d7eFxWB0iECzoPe0aMYlBQ--SpeechNoise2--Appliances-mic.wav'

    audio_1, _ = librosa.load(audio_path, sr=sampling_rate)
    # audio_1 = librosa.resample(audio_1, orig_sr=16000, target_sr=8000, res_type='soxr_vhq')
    # audio_1 = librosa.resample(audio_1, orig_sr=8000, target_sr=16000)
    # audio_2, _ = librosa.load(os.path.join('/home/yxlu/datasets/dataset_se/testset_clean', index), sr=sampling_rate)
    # audio_3, _ = librosa.load(os.path.join('generated_files/denoising/CMGAN/CMGAN_denoising', index), sr=sampling_rate)
    # audio_4, _ = librosa.load(os.path.join('generated_files/denoising/Ablation_else/MP-SENet_conformer', index), sr=sampling_rate)
    # audio_5, _ = librosa.load(os.path.join('generated_files/denoising/MP-SENet/MP-SENet', index), sr=sampling_rate)

    # 截取音频片段
    # audio_1, audio_2, audio_3, audio_4, audio_5 = audio_1[8000: ], audio_2[8000: ], audio_3[8000: ], audio_4[8000: ], audio_5[8000: ]

    # 计算音频的短时傅里叶变换（STFT）
    stft_1 = librosa.stft(audio_1, win_length=600, hop_length=50)
    # stft_2 = librosa.stft(audio_2, win_length=600, hop_length=50)
    # stft_3 = librosa.stft(audio_3, win_length=600, hop_length=50)
    # stft_4 = librosa.stft(audio_4, win_length=600, hop_length=50)
    # stft_5 = librosa.stft(audio_5, win_length=600, hop_length=50)

    # 将幅度谱转换为分贝刻度
    spec_1 = librosa.amplitude_to_db(abs(stft_1))
    # spec_2 = librosa.amplitude_to_db(abs(stft_2))
    # spec_3 = librosa.amplitude_to_db(abs(stft_3))
    # spec_4 = librosa.amplitude_to_db(abs(stft_4))
    # spec_5 = librosa.amplitude_to_db(abs(stft_5))

    # plot_spec(spec_1, 'MP-SENet')
    # plot_spec(spec_2, 'MP-SENet_wo_phase_loss')
    # plot_spec(spec_3, 'MP-SENet_wo_phase_dec')
    # plot_spec(spec_4, 'specs/specs_ablation_2kto16k/AP-BWE_wo_GAN')

    # plot_multi_spec(spec_1, spec_2, spec_3, spec_4, spec_5)
    plot_spec(spec_1, 'enhanced')
    print("图片保存路径：", os.path.abspath('enhanced.png'))

if __name__ == '__main__':
    main()